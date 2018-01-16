from sqlalchemy import Boolean, Column, String, Text, DateTime, Integer

from DivvyDb.DbObjects.base import Base
from DivvyDb.DbObjects.mixins import AbstractListable

class ValidImage(Base, AbstractListable):
    __tablename__ = "ValidImages"
    region_name = Column(String, primary_key=True)
    image_id = Column(String, primary_key=True)

    def __init__(self, region_name, image_id):
        self.region_name = region_name
        self.image_id = image_id

    def __repr__(self):
        return "ValidImage(image_id='%s')" % (self.image_id)
