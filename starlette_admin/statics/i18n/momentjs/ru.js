moment.locale('ru', {
  months : [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
  ],
  monthsShort : [
    "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
    "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
  ],
  weekdays : [
    "Воскресенье", "Понедельник", "Вторник", "Среда",
    "Четверг", "Пятница", "Суббота"
  ],
  weekdaysShort : ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
  weekdaysMin : ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
  longDateFormat : {
    LT : "HH:mm",
    LTS : "HH:mm:ss",
    L : "DD.MM.YYYY",
    LL : "D MMMM YYYY г.",
    LLL : "D MMMM YYYY г., LT",
    LLLL : "dddd, D MMMM YYYY г., LT"
  },
  calendar : {
    sameDay: '[Сегодня в] LT',
    nextDay: '[Завтра в] LT',
    lastDay: '[Вчера в] LT',
    nextWeek: function () {
      return this.day() === 1 ? '[Во] dddd [в] LT' : '[В] dddd [в] LT';
    },
    lastWeek: function () {
      switch (this.day()) {
        case 0:
          return '[В прошлое] dddd [в] LT';
        case 1:
        case 2:
        case 4:
          return '[В прошлый] dddd [в] LT';
        case 3:
        case 5:
        case 6:
          return '[В прошлую] dddd [в] LT';
      }
    },
    sameElse: 'L'
  },
  relativeTime : {
    future : "через %s",
    past : "%s назад",
    s : "несколько секунд",
    ss : "%d секунд",
    m : "минута",
    mm : "%d минут",
    h : "час",
    hh : "%d часов",
    d : "день",
    dd : "%d дней",
    M : "месяц",
    MM : "%d месяцев",
    y : "год",
    yy : "%d лет"
  },
  dayOfMonthOrdinalParse: /d{1,2}-(й|го|я)/,
  ordinal: function (number, period) {
    switch (period) {
      case 'M':
      case 'd':
      case 'DDD':
        return number + '-й';
      case 'D':
        return number + '-го';
      case 'w':
      case 'W':
        return number + '-я';
      default:
        return number;
    }
  },
  week : {
    dow : 1, // Monday is the first day of the week.
    doy : 4  // The week that contains Jan 4th is the first week of the year.
  }
});
