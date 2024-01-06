Before RUN create config.ini in root folder with following content:
[GENERAL]
UsersForPrintCount = 15
SendMsgDelay = 0.1
SendMsgRepeatCount = 50
SendMsgGroupCount = 20

[BOT]
Token = __token__
Username = __username__ # optional
Password = __password__ # optional

[MESSAGES]
SignalSearchDelay = 60
ResetSeisWaitTime = 600

[MARKET]
MinTimeZoneHours = 10
MaxTimeZoneHours = 23
TrialDays = 1

[ADMIN]
ManagerUsername = __username__
TesterIds = [__array_with_telegram_ids__]
ManagersIds = [__array_with_telegram_ids__]
