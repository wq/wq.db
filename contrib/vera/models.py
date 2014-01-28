from wq.db.patterns import models
import swapper
from django.db.models.signals import post_save
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import receiver
from django.conf import settings
from collections import OrderedDict
from .compat import clone_field

swapper.set_app_prefix('vera', 'WQ')
MODELS = swapper.get_model_names(
    'vera', ('Site', 'Event', 'Report', 'ReportStatus', 'Parameter', 'Result')
)

VALID_REPORT_ORDER = getattr(settings, "WQ_VALID_REPORT_ORDER", ('-entered',))
# Base classes for Site-Event-Report-Attribute-Value pattern
# Extend these when swapping out default implementation (below)


class BaseSite(models.NaturalKeyModel):
    @property
    def valid_events(self):
        events = self.event_set.filter(
            report__status__is_valid=True
        ).values_list('pk', flat=True)
        # FIXME: events may be duplicated
        return self.event_set.filter(pk__in=events)

    class Meta:
        abstract = True


class BaseEvent(models.NaturalKeyModel):
    site = models.ForeignKey(MODELS['Site'], null=True, blank=True)

    @property
    def valid_reports(self):
        return self.report_set.filter(status__is_valid=True).order_by(
            *VALID_REPORT_ORDER
        )

    @property
    def vals(self):
        return OrderedDict([
            (a.type.natural_key()[0], a.value)
            for a in self.results
        ])

    # Valid results for this event
    @property
    def results(self):
        Result = swapper.load_model('vera', 'Result')
        Parameter = swapper.load_model('vera', 'Parameter')
        # ORDER BY parameter, then valid report order
        order = (nest_ordering('type', Parameter._meta.ordering)
                 + ['type__id']
                 + nest_ordering('report', VALID_REPORT_ORDER))
        # DISTINCT ON parameter, collapsing multiple reports into one
        distinct = (nest_ordering('type', Parameter._meta.ordering, True)
                    + ['type__id'])
        results = Result.objects.filter(
            report__in=self.valid_reports,
            empty=False
        ).order_by(*order).distinct(*distinct)
        return results

    @property
    def is_valid(self):
        return self.valid_reports.count() > 0

    class Meta:
        abstract = True


class ReportManager(models.RelatedModelManager):
    def create_report(self, event_key, values, **kwargs):
        Event = swapper.load_model('vera', 'Event')
        kwargs['event'] = Event.objects.find(*event_key)
        report = self.create(**kwargs)
        report.vals = values
        return report


class ValidReportManager(ReportManager):
    def get_queryset(self):
        qs = super(ValidReportManager, self)
        return qs.filter(status__is_valid=True).order_by(*VALID_REPORT_ORDER)


class BaseReport(models.RelatedModel):
    event = models.ForeignKey(MODELS['Event'])
    entered = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,

        # Needed for model swapping in tests
        related_name="%(app_label)s_%(class)s",
    )
    status = models.ForeignKey(MODELS['ReportStatus'], null=True, blank=True)

    objects = ReportManager()
    valid_objects = ValidReportManager()

    @property
    def is_valid(self):
        return self.status and self.status.is_valid

    @property
    def vals(self):
        vals = OrderedDict()
        for result in self.results.all():
            vals[result.type.natural_key()[0]] = result.value
        return vals

    @vals.setter
    def vals(self, vals):
        Parameter = swapper.load_model('vera', 'Parameter')
        keys = [(key,) for key in vals.keys()]
        params, success = Parameter.objects.resolve_keys(keys)
        if not success:
            missing = [
                name for name, params in params.items() if params is None
            ]
            raise TypeError(
                "Could not identify one or more parameters: %s!"
                % missing
            )

        for key, param in params.items():
            result, is_new = self.results.get_or_create(type=param)
            result.value = vals[key[0]]
            result.save()

    def __unicode__(self):
        if self.pk is not None:
            return "%s according to %s" % (self.event, self.user)
        else:
            return "New Report"

    class Meta:
        abstract = True
        ordering = VALID_REPORT_ORDER


class BaseReportStatus(models.NaturalKeyModel):
    slug = models.SlugField()
    name = models.CharField(max_length=255)
    is_valid = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        unique_together = [['slug']]


class BaseParameter(models.IdentifiedRelatedModel):
    name = models.CharField(max_length=255)
    is_numeric = models.BooleanField(default=False)
    units = models.CharField(max_length=50, null=True, blank=True)

    def __unicode__(self):
        if self.units:
            return u"%s (%s)" % (self.name, self.units)
        else:
            return self.name

    class Meta:
        abstract = True
        ordering = ('name',)


class BaseResult(models.Model):
    type = models.ForeignKey(MODELS['Parameter'])
    report = models.ForeignKey(MODELS['Report'], related_name='results')
    value_numeric = models.FloatField(null=True, blank=True)
    value_text = models.TextField(null=True, blank=True)
    empty = models.BooleanField(default=False, db_index=True)

    def is_empty(self, value):
        if value is None:
            return True
        if isinstance(value, basestring) and len(value.strip()) == 0:
            return True
        return False

    @property
    def value(self):
        if self.type.is_numeric:
            return self.value_numeric
        return self.value_text

    @value.setter
    def value(self, val):
        self.empty = self.is_empty(val)
        if self.type.is_numeric:
            if self.empty:
                self.value_numeric = None
            else:
                self.value_numeric = val
        else:
            self.value_text = val

    def __unicode__(self):
        return "%s -> %s: %s" % (self.report, self.type, self.value)

    class Meta:
        abstract = True
        ordering = ('type',)
        index_together = [
            ('type', 'report', 'empty'),
        ]


# Denormalize Events with Results from valid Reports
class EventResultManager(models.Manager):
    def set_for_event(self, event, delete=True):
        self.filter(event=event).delete()
        for result in event.results:
            er = self.model(
                event=event,
                result=result
            )
            er.save()

    def set_for_events(self, events, delete=True):
        for event in events:
            self.set_for_event(event, delete)

    def set_all(self):
        self.all().delete()
        Event = swapper.load_model('vera', 'Event')
        self.set_for_events(Event.objects.all(), delete=False)


class BaseEventResult(models.Model):
    """
    Denormalized event-result pairs (for valid reports)
    """
    id = models.PositiveIntegerField(primary_key=True)
    event = models.ForeignKey(MODELS['Event'])
    result = models.ForeignKey(MODELS['Result'])
    objects = EventResultManager()

    def __unicode__(self):
        if self.result_value_numeric is not None:
            value = self.result_value_numeric
        else:
            value = self.result_value_text
        return "%s -> %s: %s" % (
            self.event,
            self.result_type,
            value
        )

    def save(self, *args, **kwargs):
        """
        Denormalize all properties from the event and the result.
        """
        if self.event_id is None or self.result_id is None:
            return
        self.pk = self.result.pk

        def set_value(src, name):
            if field.primary_key:
                return
            obj = getattr(self, src)
            setattr(self, src + '_' + name, getattr(obj, name))

        for field in self.event._meta.fields:
            set_value('event', field.name)
        for field in self.result._meta.fields:
            set_value('result', field.name)
        super(BaseEventResult, self).save(*args, **kwargs)

    class Meta:
        abstract = True


def create_eventresult_model(event_cls, result_cls,
                             base=BaseEventResult, swappable=False):
    """
    **Here be magic**

    EventResult needs to have all of the fields from Event and Result.
    In order to DRY (and since either of these classes may be swapped), we
    add the fields dynamically here.  If neither Event or Result are swapped,
    this function will be called below, otherwise the user should call
    this function in their models.py.
    """

    app = 'vera'
    module = base.__module__
    for cls in event_cls, result_cls, base:
        if cls._meta.app_label != 'vera':
            app = cls._meta.app_label
            module = cls.__module__

    class Meta(base.Meta):
        db_table = 'wq_eventresult'
        unique_together = ('event', 'result_type')
        app_label = app

    if swappable:
        Meta.swappable = swappable

    attrs = {
        'Meta': Meta,
        '__module__': module
    }

    def add_field(prefix, field):
        if field.primary_key:
            return
        attrs[prefix + '_' + field.name] = clone_field(field)

    for field in event_cls._meta.fields:
        add_field('event', field)

    for field in result_cls._meta.fields:
        add_field('result', field)

    EventResult = type(
        'EventResult',
        (base,),
        attrs
    )

    @receiver(post_save, weak=False, dispatch_uid="eventresult_receiver")
    def handler(sender, instance=None, **kwargs):
        events = find_events(instance)
        if events:
            EventResult.objects.set_for_events(events)

    return EventResult


# Default implementation of the above classes, can be swapped
class Site(BaseSite):
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return "%s, %s" % (round(self.latitude, 3), round(self.longitude, 3))

    class Meta(BaseSite.Meta):
        db_table = 'wq_site'
        swappable = swapper.swappable_setting('vera', 'Site')
        unique_together = ('latitude', 'longitude')


class Event(BaseEvent):
    date = models.DateField()

    def __unicode__(self):
        return "%s on %s" % (self.site, self.date)

    class Meta(BaseEvent.Meta):
        db_table = 'wq_event'
        swappable = swapper.swappable_setting('vera', 'Event')
        unique_together = ('site', 'date')
        ordering = ('-date',)


class Report(BaseReport):
    class Meta(BaseReport.Meta):
        db_table = 'wq_report'
        swappable = swapper.swappable_setting('vera', 'Report')


class ReportStatus(BaseReportStatus):
    class Meta(BaseReportStatus.Meta):
        verbose_name_plural = 'report statuses'
        db_table = 'wq_reportstatus'
        swappable = swapper.swappable_setting('vera', 'ReportStatus')


class Parameter(BaseParameter):
    class Meta(BaseParameter.Meta):
        db_table = 'wq_parameter'
        swappable = swapper.swappable_setting('vera', 'Parameter')


class Result(BaseResult):
    class Meta(BaseResult.Meta):
        db_table = 'wq_result'
        swappable = swapper.swappable_setting('vera', 'Result')


EventResult = create_eventresult_model(
    Event, Result, swappable=swapper.swappable_setting('vera', 'EventResult')
)

if (swapper.is_swapped('vera', 'Event')
        and swapper.is_swapped('vera', 'Result')
        and not swapper.is_swapped('vera', 'EventResult')):
    raise ImproperlyConfigured(
        "Event or Result was swapped but EventResult was not!"
    )


def nest_ordering(prefix, ordering, ignore_reverse=False):
    nest_order = []
    for field in ordering:
        reverse = ''
        if field.startswith('-'):
            field = field[1:]
            if not ignore_reverse:
                reverse = '-'
        nest_order.append(reverse + prefix + '__' + field)
    return nest_order


def find_events(instance):
    if isinstance(instance, BaseEvent):
        return [instance]
    if isinstance(instance, BaseReport):
        return [instance.event]
    if isinstance(instance, BaseResult):
        return [instance.report.event]
    return None
