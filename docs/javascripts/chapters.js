// Chapter lists for long gallery films: <ol class="mvx-chapters" data-video="ID"> with links carrying data-t
// (seconds). A click seeks the video and plays; the chapter playing is marked as it goes; ?t=SECONDS in the
// address opens the page at that moment. Works with instant navigation (document$) and without it.
(function () {
  function setup() {
    document.querySelectorAll("ol.mvx-chapters[data-video]").forEach(function (list) {
      if (list.dataset.ready) return;
      list.dataset.ready = "1";
      var video = document.getElementById(list.dataset.video);
      if (!video) return;
      var links = Array.prototype.slice.call(list.querySelectorAll("a[data-t]"));
      var times = links.map(function (a) { return parseFloat(a.dataset.t); });

      function seek(t) {
        var go = function () {
          video.currentTime = t;
          var p = video.play();
          if (p && p.catch) p.catch(function () {});
        };
        if (video.readyState >= 1) go();
        else video.addEventListener("loadedmetadata", go, { once: true });
      }

      function mark() {
        var now = video.currentTime, k = 0;
        for (var i = 0; i < times.length; i++) if (now + 0.25 >= times[i]) k = i;
        links.forEach(function (a, i) {
          if (i === k) a.setAttribute("aria-current", "true");
          else a.removeAttribute("aria-current");
        });
      }

      links.forEach(function (a) {
        a.addEventListener("click", function (e) {
          e.preventDefault();
          seek(parseFloat(a.dataset.t));
          var u = new URL(location.href);
          u.searchParams.set("t", Math.round(parseFloat(a.dataset.t)));
          history.replaceState(history.state, "", u);
          video.scrollIntoView({ behavior: "smooth", block: "nearest" });
        });
      });
      video.addEventListener("timeupdate", mark);
      video.addEventListener("seeked", mark);
      mark();

      var start = new URLSearchParams(location.search).get("t");
      var m = start && /^\d+(?:\.\d+)?$/.test(start) ? [null, start] : null;
      if (m) {
        video.preload = "auto";
        video.addEventListener("loadedmetadata", function () { video.currentTime = parseFloat(m[1]); mark(); },
                               { once: true });
      }
    });
  }

  if (typeof document$ !== "undefined" && document$.subscribe) document$.subscribe(setup);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", setup);
  else setup();
})();
