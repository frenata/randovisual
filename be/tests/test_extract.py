import pytest
import sqlalchemy as sql
import vcr

from randovisual.db import models

@pytest.fixture
def rider(conn):
    conn.execute(sql.insert(models.Member).values(id=14039))
    conn.commit()

@vcr.use_cassette()
def test_extract_rider(rider, conn, app):
    before = conn.execute(sql.select(models.Route)).mappings().all()
    res = app.get("/extract/rusa/rider/14039")
    after = conn.execute(sql.select(models.Route)).mappings().all()

    assert res.text == "26", "26 routes extracted"
    assert len(before) + int(res.text) == len(after), "db should have all the extracted routes"


@vcr.use_cassette()
def test_extract_year(conn, app):
    before = conn.execute(sql.select(models.Member)).mappings().all()
    res = app.get("/extract/rusa/year/1999")
    after = conn.execute(sql.select(models.Member)).mappings().all()

    assert res.text == "3", "3 riders extracted"
    assert len(before) + int(res.text) == len(after), "db should have all the extracted members"


@vcr.use_cassette()
def test_extract_brevet(conn, app):
    before = conn.execute(sql.select(models.Route)).mappings().all()
    res = app.get("/extract/rusa/route/brevet/1405?rwgps_id=13704022&category=ACPB")
    after = conn.execute(sql.select(models.Route)).mappings().all()

    assert len(before) + 1 == len(after), "db should have extracted a new route"
