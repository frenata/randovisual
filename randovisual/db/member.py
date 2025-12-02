import datetime
from geoalchemy2 import Geometry
from randovisual.db import Base
from typing import List
from typing import Optional
from sqlalchemy import ARRAY, Text, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Member(Base):
    __tablename__ = "rusa_member"
    id: Mapped[int] = mapped_column(primary_key=True)
    names: Mapped[list[str]] = mapped_column(ARRAY(Text))
    years: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    def __repr__(self) -> str:
        return f"Member(id={self.id!r})"


class Ride(Base):
    __tablename__ = "ride"
    rusa_id: Mapped[int] = mapped_column(primary_key=True)
    duration: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    rider_id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(primary_key=True)


class Route(Base):
    __tablename__ = "route"
    rusa_id: Mapped[int] = mapped_column(primary_key=True)
    rwgps_id: Mapped[int] = mapped_column()
    geometry: Mapped[Geometry] = mapped_column(Geometry('GEOMETRY', srid=4326))
    name: Mapped[str] = mapped_column(Text)
    climbing: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(Text, primary_key=True)
