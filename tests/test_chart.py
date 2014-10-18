from rest_framework.test import APITestCase
from rest_pandas.test import parse_csv
from tests.chart_app.models import Series, Value


class ChartTestCase(APITestCase):
    def setUp(self):
        data = (
            ('2014-01-01', 'Series1', 'temp', 0.5),
            ('2014-01-02', 'Series1', 'temp', 0.4),
            ('2014-01-03', 'Series1', 'temp', 0.6),
            ('2014-01-04', 'Series1', 'temp', 0.2),
            ('2014-01-05', 'Series1', 'temp', 0.1),

            ('2014-01-01', 'Series2', 'temp', 0.4),
            ('2014-01-02', 'Series2', 'temp', 0.3),
            ('2014-01-03', 'Series2', 'temp', 0.6),
            ('2014-01-04', 'Series2', 'temp', 0.7),
            ('2014-01-05', 'Series2', 'temp', 0.2),

            ('2014-01-01', 'Series2', 'snow', 0.1),
            ('2014-01-02', 'Series2', 'snow', 0.0),
            ('2014-01-03', 'Series2', 'snow', 0.3),
            ('2014-01-04', 'Series2', 'snow', 0.0),
            ('2014-01-05', 'Series2', 'snow', 0.0),
        )

        for date, series, param, value in data:
            Value.objects.create(
                date=date,
                series=Series.objects.find(series),
                parameter=param,
                units="-",
                value=value,
            )

    def test_timeseries(self):
        response = self.client.get(
            "/chart/series1/series2/temp/timeseries.csv"
        )
        datasets = self.parse_csv(response)
        self.assertEqual(len(datasets), 2)
        for dataset in datasets:
            self.assertEqual(dataset['parameter'], 'temp')
            self.assertEqual(dataset['units'], '-')
            self.assertEqual(len(dataset['data']), 5)

        if datasets[0]['series'] == "series1":
            s1data = datasets[0]
        else:
            s1data = datasets[1]

        self.assertEqual(s1data['series'], "series1")
        d0 = s1data['data'][0]
        self.assertEqual(d0['date'], '2014-01-01')
        self.assertEqual(d0['value'], 0.5)

    def test_scatter(self):
        response = self.client.get("/chart/series2/temp/snow/scatter.csv")

        datasets = self.parse_csv(response)
        self.assertEqual(len(datasets), 1)

        dataset = datasets[0]
        self.assertEqual(dataset['series'], 'series2')
        self.assertEqual(len(dataset['data']), 5)

        d4 = dataset['data'][4]
        self.assertEqual(d4['date'], '2014-01-05')
        self.assertEqual(d4['temp'], 0.2)
        self.assertEqual(d4['snow'], 0.0)

    def test_boxplot(self):
        response = self.client.get("/chart/series1/temp/boxplot.csv")

        datasets = self.parse_csv(response)
        self.assertEqual(len(datasets), 1)

        dataset = datasets[0]
        self.assertEqual(dataset['series'], 'series1')
        self.assertEqual(len(dataset['data']), 1)

        stats = dataset['data'][0]
        self.assertEqual(stats['year'], '2014')
        self.assertEqual(stats['min'], 0.1)
        self.assertEqual(stats['mean'], 0.36)
        self.assertEqual(stats['max'], 0.6)

    def parse_csv(self, response):
        return parse_csv(response.content.decode('utf-8'))
