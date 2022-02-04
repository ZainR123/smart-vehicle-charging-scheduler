import django_tables2 as tables
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import User
from django.db import models


class GetCarModel(models.Model):
    Car_Model = models.CharField(max_length=100)

    class Meta:
        db_table = "cardata"


class UserDatabase(models.Model):
    id = models.IntegerField(primary_key=True)
    Username = models.CharField(max_length=45)
    Car = models.CharField(max_length=100, verbose_name="User Vehicle")
    Current_Charge = models.IntegerField(verbose_name="Current Vehicle Charge")
    Preferred_Charge_Station = models.IntegerField(
        verbose_name="Charging Station")
    Preferred_Start_Datetime = models.DateTimeField(
        verbose_name="Preferred Start Datetime")
    Preferred_End_Datetime = models.DateTimeField(
        verbose_name="Preferred End Datetime")
    Preferred_Charge_Level = models.IntegerField(
        verbose_name="Preferred Charging Level")
    Scheduled_Datetime_Start = models.DateTimeField(
        verbose_name="Allocated Charging Start Datetime")
    Scheduled_Datetime_End = models.DateTimeField(
        verbose_name="Allocated Charging End Datetime")
    Charging_Station = models.IntegerField(
        verbose_name="Allocated Charging Station")
    Final_Charge = models.IntegerField(verbose_name="Max Charge During Slot")
    Is_Scheduling = models.BooleanField()
    Arrival = models.DateTimeField(verbose_name="Arrival Datetime")
    Slot_Taken = models.BooleanField()
    New_Sugg_Start = models.DateTimeField()
    New_Sugg_End = models.DateTimeField()
    Error = models.IntegerField()

    class Meta:
        db_table = "userdata"


class UserTable(tables.Table):
    class Meta:
        model = UserDatabase
        attrs = {'width': '100%'}
        exclude = (
            "Is_Scheduling", "id", "Charging_Station", "Car", "Slot_Taken",
            "New_Sugg_Start", "New_Sugg_End", "Error")
        sequence = ("Username", "Current_Charge", "Preferred_Charge_Level",
                    "Preferred_Start_Datetime", "Preferred_End_Datetime",
                    "Preferred_Charge_Station",
                    "Scheduled_Datetime_Start", "Scheduled_Datetime_End",
                    "Final_Charge")


class ManagerDatabase(models.Model):
    id = models.IntegerField(primary_key=True)
    Username = models.CharField(max_length=45)

    class Meta:
        db_table = "managerdata"
