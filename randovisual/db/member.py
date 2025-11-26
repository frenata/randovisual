import datetime
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
    id: Mapped[int] = mapped_column(primary_key=True)
    duration: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    rider_id: Mapped[int] = mapped_column(primary_key=True)
