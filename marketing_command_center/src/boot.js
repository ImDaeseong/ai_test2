/* Classic (non-module) script: shows a visible banner when the app script fails to load or run, so a blank page explains itself. */
(function () {
  var problems = [];
  function show() {
    var box = document.getElementById("bootProblem");
    if (!box || !problems.length) return;
    box.hidden = false;
    box.textContent = "화면이 정상으로 로드되지 않았습니다. Ctrl+F5로 새로 고침하고, 계속되면 이 문구를 알려 주세요: " + problems.join(" | ");
  }
  function report(text) {
    problems.push(text);
    show();
  }
  window.addEventListener("error", function (event) {
    report(event.message || "script error");
  });
  window.addEventListener("unhandledrejection", function (event) {
    report(String(event.reason));
  });
  window.addEventListener("load", function () {
    setTimeout(function () {
      if (document.body.getAttribute("data-ready") !== "1") report("앱 스크립트가 실행되지 않았습니다 (" + navigator.userAgent + ")");
      else show();
    }, 1500);
  });
})();
