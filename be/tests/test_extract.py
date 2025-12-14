import vcr
import sqlalchemy as sql
import randovisual.db.models as models
import randovisual.api.extract as sut

@vcr.use_cassette()
def test_extract_rider(conn, app):
    conn.execute(sql.insert(models.Member).values(id=14039))
    conn.commit()
    res = app.get("/extract/rusa/rider/14039")
    assert res.text == '26', "26 routes extracted"
