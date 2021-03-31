from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, Text, Boolean, Date, Time, ARRAY

g_Base = declarative_base()


def create_all_tbl(sqlite_eng):
    g_Base.metadata.create_all(sqlite_eng, checkfirst=True)


class rule_main_tbl(g_Base):
    __tablename__ = 'rule_main_tbl'
    uuid = Column(Text, nullable=False, unique=True, primary_key=True)
    enable = Column(Boolean, nullable=False)
    type = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False)
    script_path = Column(Text, nullable=False)
    py_path = Column(Text, nullable=False)


class rule_date_tbl(g_Base):
    __tablename__ = 'rule_date_tbl'
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    uuid = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)


class rule_time_tbl(g_Base):
    __tablename__ = 'rule_time_tbl'
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    uuid = Column(Text, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)


class rule_src_device_tbl(g_Base):
    __tablename__ = 'rule_src_device_tbl'
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    uuid = Column(Text, nullable=False)
    src_device = Column(Text, nullable=False)


class rule_dst_device_tbl(g_Base):
    __tablename__ = 'rule_dst_device_tbl'
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    uuid = Column(Text, nullable=False)
    dst_device = Column(Text, nullable=False)


class rule_command_run_tbl(g_Base):
    __tablename__ = 'rule_command_run_tbl'
    device_id = Column(Text, nullable=False, unique=True, primary_key=True)
    cmd_list = Column(Text, nullable=False)
    # cmd_list = Column(Text, nullable=False)
