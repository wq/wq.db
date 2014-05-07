from wq.db.rest import app
import swapper
from .serializers import EventSerializer, ReportSerializer, ResultSerializer

Event = swapper.load_model('vera', 'Event')
Report = swapper.load_model('vera', 'Report')
ReportStatus = swapper.load_model('vera', 'ReportStatus')
Result = swapper.load_model('vera', 'Result')

app.router.register_model(Event, serializer=EventSerializer)
app.router.register_model(Report, serializer=ReportSerializer)
app.router.register_model(ReportStatus, lookup='slug')
app.router.register_model(Result, serializer=ResultSerializer)
