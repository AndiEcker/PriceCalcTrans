'''
    public application constants

Created on 01-Feb-2012
- V1.0     02-Mar-2012
- V1.1     08-Mar-2012
- V1.2     08-May-2012   additional conditions and actions. 
- V1.3     31-Aug-2012   corrected intersection condition (ResFrom < RangeTo and ResTo > RangeFrom)
                         into: ResFrom <= RangeTo and ResTo > RangeFrom;
                         corrected Percentage@ date range condition
                         (ResFrom + (day - 1) >= RangeFrom and ResFrom + (day - 1) <= RangeTo)
                         into: ResFrom + day >= RangeFrom and ResFrom + (day - 1) <= RangeTo.
- V1.4     06-Oct-2012   work around os.time summer/winter time switch correction. added
                         rounding/floor into days/integer for lua date/double values.
                         (lua os.time date values like e.g. Sihot parameter sts_fromdate
                          are numeric/double second values. Unfortunately os.time is
                          correcting this value by one hour (3600 s) on switch-over
                          between summer and winter time. Therefore the lua expression:
                               dateX + 1 day = dayafter
                          will fail if dateX lies on switch-over day and before the switch-over time.
                            -- this example fails:
                            os.time{year=2012, month=10, day=27} + 24*60*60
                              = os.time{year=2012, month=10, day=28}
                            -- whereas the following expression results in true:
                            os.time{year=2012, month=10, day=28} + 24*60*60
                              = os.time{year=2012, month=10, day=29}
                          On top of that lua's os.time is defaulting to 12am/midday instead of
                          12pm/midnight when no hour/min/sec argument is specified.) 
 V1.5      08-Oct-2012   bug fix (integer rounding was missing for 2nd reselling date).
 V1.6      09-May-2013   Added new condition (sold min days before arrival date range).
 V2.0      13-May-2013   Moved conditions and actions into external config/ini file.
 V3.0      02-Mar-2014   Fixed bug with config file (rules display showing hard-coded cond/actions instead of the ones from cfg file)
                         and refactored lua script header from using string coding instead of pickle. 
                                
@author: andi
'''
APP_TITLE = 'SiHOT Price Calculation Rules Transformer'
APP_VERSION = '3.0'

