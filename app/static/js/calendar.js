document.addEventListener('DOMContentLoaded', function () {
  if (window.calendar && !window.eventsLoaded) {
    fetch('/reminders/api/events')
      .then(res => res.json())
      .then(events => {
        console.log("Events loaded:", events);
        if (Array.isArray(events)) {
          console.log("Event count:", events.length);
          if (events.length > 0) {
            window.calendar.addEventSource(events);
          } else {
            console.warn("No events returned from API");
          }
        } else {
          console.error("Invalid events data:", events);
        }
        window.eventsLoaded = true;
      });
  }
});
