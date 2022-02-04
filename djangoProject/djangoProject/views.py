from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.utils import timezone

from djangoProject.forms import CreateUserForm
from djangoProject.models import GetCarModel, UserDatabase, ManagerDatabase, \
    UserTable


def time_to_minutes(s):
    t = 0
    for u in s.split(':'):
        t = 60 * t + int(u)
    return t


def discretise_time(t):
    rem = t % 15
    if rem == 0:
        return t

    if rem < round(15 / 2):
        return t - rem
    else:
        return t + 15 - rem


def home(request):
    return render(request, 'home.html')


def login_page(request):
    current_user = request.user.username
    if request.user.is_authenticated and ManagerDatabase.objects.filter(
            Username=current_user).exists():
        return redirect('managerHome')
    elif request.user.is_authenticated and UserDatabase.objects.filter(
            Username=current_user).exists():
        return redirect('userHome')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None and ManagerDatabase.objects.filter(
                    Username=username).exists() and 'managerSubmit' in request.POST:
                login(request, user)
                return redirect('managerHome')
            elif user is not None and UserDatabase.objects.filter(
                    Username=username).exists() and 'userSubmit' in request.POST:
                login(request, user)
                return redirect('userHome')
            else:
                messages.info(request, 'Username OR password is incorrect')

        return render(request, 'login.html')


def logout_page(request):
    logout(request)
    return redirect('login')


def change_car_model(request):
    results = GetCarModel.objects.all()
    current_user = request.user.username
    filterObj = UserDatabase.objects.get(Username=current_user)
    if request.method == 'POST':
        if request.POST.get('Car'):
            filterObj.Car = request.POST.get('Car')
            filterObj.save()
            messages.success(request, 'Car successfully changed')
        else:
            messages.info(request, "Please select a vehicle")

    context = {'currentUser': current_user, 'Car': results}
    return render(request, 'changeCarModel.html', context)


def register(request):
    results = GetCarModel.objects.all()
    if request.user.is_authenticated:
        return redirect('login')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid() and request.POST.get('Car'):
                form.save()
                saveRecord = UserDatabase()
                user = form.cleaned_data.get('username')
                placeholder = "1234-12-23 11:23:40"
                placeholder = timezone.make_aware(
                    datetime.fromisoformat(placeholder),
                    timezone.get_default_timezone())
                saveRecord.Username = user
                saveRecord.Car = request.POST.get('Car')
                saveRecord.save()
                filterObj = UserDatabase.objects.get(Username=user)
                filterObj.Scheduled_Datetime_Start = placeholder
                filterObj.Scheduled_Datetime_End = placeholder
                filterObj.Arrival = placeholder
                filterObj.Preferred_Start_Datetime = placeholder
                filterObj.Preferred_End_Datetime = placeholder
                filterObj.save()
                messages.success(request,
                                 'Account was created for User: ' + user)

                return redirect('login')
            else:
                if form.is_valid() is True:
                    messages.info(request, "Please select a vehicle")

        context = {'form': form, 'Car': results}
        return render(request, 'register.html', context)


def manager_register(request):
    if request.user.is_authenticated:
        return redirect('login')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                saveRecord = ManagerDatabase()
                user = form.cleaned_data.get('username')
                saveRecord.Username = user
                saveRecord.save()
                messages.success(request,
                                 'Account was created for Manager: ' + user)
                return redirect('login')

        context = {'form': form}
        return render(request, 'managerRegister.html', context)


def user_home(request):
    error = False
    chargeWrong = False
    current_user = request.user.username
    filterObj = UserDatabase.objects.get(Username=current_user)

    current = timezone.make_aware(datetime.now(),
                                  timezone.get_default_timezone())

    finalDate = current + relativedelta(months=+1)
    finalDate = finalDate.strftime("%Y-%m-%dT%H:%M")

    now = current.strftime("%Y-%m-%dT%H:%M")

    if request.method == 'POST':

        if 'freeSlot' in request.POST:
            placeholder = "1234-12-23 11:23:40"
            placeholder = timezone.make_aware(
                datetime.fromisoformat(placeholder),
                timezone.get_default_timezone())
            filterObj.Scheduled_Datetime_Start = placeholder
            filterObj.Scheduled_Datetime_End = placeholder
            filterObj.save()
            messages.success(request, "Slot successfully freed")
        else:

            startDatetime = timezone.make_aware(
                datetime.fromisoformat(request.POST.get('startDate')),
                timezone.get_default_timezone())
            endDatetime = timezone.make_aware(
                datetime.fromisoformat(request.POST.get('endDate')),
                timezone.get_default_timezone())
            startDatetimeUpper = startDatetime + timedelta(hours=6)
            startDatetimeLower = startDatetime + timedelta(minutes=15)

            if startDatetime > endDatetime:
                messages.error(request,
                               "Please enter an end datetime greater than the start datetime.")
                error = True

            if startDatetimeUpper < endDatetime:
                messages.error(request,
                               "Please enter an end time which is a max of 3 hours greater than the start time.")
                error = True

            if startDatetimeLower > endDatetime:
                messages.error(request,
                               "Please enter an end time which is at minimum 15 minutes greater than the start time.")
                error = True

            if request.POST.get('currentCharge') >= request.POST.get(
                    'prefCharge'):
                messages.error(request,
                               "Please enter a preferred charge higher than your current charge.")
                error = True
                chargeWrong = True

            if int(request.POST.get('prefCharge')) - int(
                    request.POST.get('currentCharge')) <= 1 and not chargeWrong:
                messages.error(request,
                               "Please enter a preferred charge with a difference greater than 1 to the current charge.")
                error = True

            if error:
                messages.error(request, "Try again.")

            elif not error:
                filterObj.Preferred_Charge_Station = request.POST.get(
                    'location')
                filterObj.Preferred_Start_Datetime = startDatetime
                filterObj.Preferred_End_Datetime = endDatetime
                filterObj.Current_Charge = request.POST.get('currentCharge')
                filterObj.Preferred_Charge_Level = request.POST.get(
                    'prefCharge')
                filterObj.Is_Scheduling = '1'
                filterObj.Arrival = current
                filterObj.save()

                isScheduled = 0

                while isScheduled == 0:
                    isScheduled = UserDatabase.objects.filter(
                        Username=current_user,
                        Is_Scheduling='0').count()

                doneSuggestion = UserDatabase.objects.filter(
                    Username=current_user,
                    Slot_Taken='1').count()
                unableToSchedule = UserDatabase.objects.filter(
                    Username=current_user, Error='1').count()

                if unableToSchedule == 1:
                    messages.error(request,
                                   "Unfortunately the scheduler wasn't able to generate a valid time for you, due to energy consumption being too high at the given time.")
                    messages.error(request,
                                   "Please enter a different preferred time and try again.")
                    userObj = UserDatabase.objects.get(Username=current_user)
                    userObj.Error = '0'
                    userObj.save()

                elif doneSuggestion == 1:
                    takenObject = UserDatabase.objects.get(
                        Username=current_user,
                        Slot_Taken='1')
                    suggestedStart = str(takenObject.New_Sugg_Start)
                    suggestedStart = suggestedStart[:19]
                    suggestedStart = datetime.strptime(suggestedStart,
                                                       '%Y-%m-%d %H:%M:%S')
                    suggestedEnd = str(takenObject.New_Sugg_End)
                    suggestedEnd = suggestedEnd[:19]
                    suggestedEnd = datetime.strptime(suggestedEnd,
                                                     '%Y-%m-%d %H:%M:%S')
                    string1 = f"Suggested start time: {suggestedStart}"
                    string2 = f"Suggested end time: {suggestedEnd}"
                    messages.error(request,
                                   "Please enter a different preferred time as your suggested time has already been taken.")
                    messages.error(request, string1)
                    messages.error(request, string2)
                    userObj = UserDatabase.objects.get(Username=current_user)
                    userObj.Slot_Taken = '0'
                    userObj.save()

                else:
                    return redirect('userScheduled')

    if filterObj.Scheduled_Datetime_End < current:
        context = {'UserDatabase': None, 'currentDate': now,
                   'finalDate': finalDate, 'currentUser': current_user}
    else:
        context = {'UserDatabase': filterObj, 'currentDate': now,
                   'finalDate': finalDate, 'currentUser': current_user}

    return render(request, 'userHome.html', context)


def user_scheduled(request):
    current_user = request.user.username
    filterObj = UserDatabase.objects.get(Username=request.user.username)
    currentCharge = int(filterObj.Current_Charge)
    prefChargeLevel = int(filterObj.Preferred_Charge_Level)
    finalCharge = int(filterObj.Final_Charge)
    difference = prefChargeLevel - currentCharge
    chargeStation = int(filterObj.Charging_Station)

    if chargeStation == 1:
        lat = 52.95423
        long = -1.18106
    else:
        lat = 52.95261
        long = -1.18268

    if difference != finalCharge:
        messages.error(request,
                       "A time has been scheduled however your preferred charge preferences weren't met")

    context = {'UserDatabase': filterObj, 'MapLat': lat, 'MapLong': long,
               'Station': chargeStation, 'currentUser': current_user}
    return render(request, 'userScheduled.html', context)


def manager_home(request):
    current_user = request.user.username
    station1 = UserTable(UserDatabase.objects.filter(Charging_Station=1))
    station2 = UserTable(UserDatabase.objects.filter(Charging_Station=2))
    context = {'table': station1, 'table2': station2,
               'currentUser': current_user}
    return render(request, 'managerHome.html', context)
