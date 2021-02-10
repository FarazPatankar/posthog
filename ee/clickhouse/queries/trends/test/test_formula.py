from typing import Dict, Optional
from uuid import uuid4

from freezegun.api import freeze_time

from ee.clickhouse.models.event import create_event
from ee.clickhouse.queries.trends.clickhouse_trends import ClickhouseTrends
from posthog.models import Person
from posthog.models.filters.filter import Filter
from posthog.queries.abstract_test.test_interval import AbstractIntervalTest
from posthog.queries.abstract_test.test_timerange import AbstractTimerangeTest
from posthog.test.base import APIBaseTest


def _create_event(**kwargs):
    kwargs.update({"event_uuid": uuid4()})
    create_event(**kwargs)


class TestFormula(AbstractIntervalTest, APIBaseTest):
    def setUp(self):
        super().setUp()  # type: ignore

        person = Person.objects.create(
            team_id=self.team.pk, distinct_ids=["blabla", "anonymous_id"], properties={"$some_prop": "some_val"}
        )
        with freeze_time("2020-01-02T13:01:01Z"):
            _create_event(
                team=self.team,
                event="session start",
                distinct_id="blabla",
                properties={"session duration": 200, "location": "Paris", "$current_url": "http://example.org"},
            )
            _create_event(
                team=self.team,
                event="session start",
                distinct_id="blabla",
                properties={"session duration": 300, "location": "Paris"},
            )
            _create_event(
                team=self.team,
                event="session start",
                distinct_id="blabla",
                properties={"session duration": 400, "location": "London"},
            )
        with freeze_time("2020-01-03T13:01:01Z"):
            _create_event(
                team=self.team,
                event="session start",
                distinct_id="blabla",
                properties={"session duration": 400, "location": "London"},
            )
        with freeze_time("2020-01-03T13:04:01Z"):
            _create_event(
                team=self.team,
                event="session start",
                distinct_id="blabla",
                properties={"session duration": 500, "location": "London"},
            )
            _create_event(
                team=self.team,
                event="session end",
                distinct_id="blabla",
                properties={"session duration": 500, "location": "London"},
            )

    def _run(self, extra: Dict = {}, run_at: Optional[str] = None):
        with freeze_time(run_at or "2020-01-04T13:01:01Z"):
            action_response = ClickhouseTrends().run(
                Filter(
                    data={
                        "events": [
                            {"id": "session start", "math": "sum", "math_property": "session duration"},
                            {"id": "session start", "math": "avg", "math_property": "session duration"},
                        ],
                        "formula": "A + B",
                        **extra,
                    }
                ),
                self.team,
            )
        return action_response

    def test_minute_interval(self):
        data = self._run({"date_from": "-1h", "interval": "minute"}, run_at="2020-01-03T13:05:01Z")[0]["data"]
        self.assertEqual(data[-2], 1000.0)
        self.assertEqual(data[-5], 800.0)

    def test_hour_interval(self):
        data = self._run({"date_from": "-1d", "interval": "hour"}, run_at="2020-01-03T13:05:01Z")[0]["data"]
        self.assertEqual(
            data,
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1200.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1350.0,
            ],
        )

    def test_day_interval(self):
        data = self._run({"date_from": "-3d"}, run_at="2020-01-03T13:05:01Z")[0]["data"]
        self.assertEqual(data, [0.0, 0.0, 1200.0, 1350.0])

    def test_week_interval(self):
        data = self._run({"date_from": "-2w", "interval": "week"}, run_at="2020-01-03T13:05:01Z")[0]["data"]
        self.assertEqual(data, [1350.0])

    def test_month_interval(self):
        data = self._run({"date_from": "-2m", "interval": "month"}, run_at="2020-01-03T13:05:01Z")[0]["data"]
        self.assertEqual(data, [0.0, 0.0, 2160.0])

    def test_interval_rounding(self):
        pass

    def test_formula(self):
        self.assertEqual(self._run({"formula": "A - B"})[0]["data"], [0.0, 0.0, 0.0, 0.0, 0.0, 600.0, 450.0, 0.0])
        self.assertEqual(self._run({"formula": "A * B"})[0]["data"], [0.0, 0.0, 0.0, 0.0, 0.0, 270000.0, 405000.0, 0.0])
        self.assertEqual(self._run({"formula": "A / B"})[0]["data"], [0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 2.0, 0.0])

    def test_breakdown(self):
        action_response = self._run({"formula": "A - B", "breakdown": "location"})
        self.assertEqual(action_response[0]["data"], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 450.0, 0.0])
        self.assertEqual(action_response[0]["label"], "London")
        self.assertEqual(action_response[1]["data"], [0.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0, 0.0])
        self.assertEqual(action_response[1]["label"], "Paris")

    def test_filtering(self):
        self.assertEqual(
            self._run({"properties": [{"key": "$current_url", "value": "http://example.org"}]})[0]["data"],
            [0.0, 0.0, 0.0, 0.0, 0.0, 400.0, 0.0, 0.0],
        )