from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Draw(Base):
    __tablename__ = 'draws'
    id = Column(Integer, primary_key=True, autoincrement=True)
    draw_date = Column(String, nullable=False)
    draw_type = Column(String, default='lunchtime', nullable=False)  # 'lunchtime' or 'teatime'
    numbers = Column(String, nullable=False)
