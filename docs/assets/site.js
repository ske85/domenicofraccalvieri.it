(function () {
  var PAGE = 20, shown = PAGE, area = "Tutti", q = "";
  var rows = Array.prototype.slice.call(document.querySelectorAll("#list li"));
  var months = Array.prototype.slice.call(document.querySelectorAll("#list [data-month]"));
  var buttons = Array.prototype.slice.call(document.querySelectorAll(".topics button"));
  var input = document.getElementById("q"), more = document.getElementById("more"), empty = document.getElementById("empty");
  var norm = function (s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); };
  rows.forEach(function (r) { r._q = norm(r.getAttribute("data-q") || ""); });

  function apply() {
    var nq = norm(q.trim()), match = 0;
    rows.forEach(function (r) {
      var ok = (area === "Tutti" || r.getAttribute("data-area") === area) && (!nq || r._q.indexOf(nq) !== -1);
      if (ok) match++;
      r.hidden = !ok || match > shown;
    });
    months.forEach(function (m) {
      var list = m.nextElementSibling, any = false;
      Array.prototype.forEach.call(list.children, function (li) { if (!li.hidden) any = true; });
      m.hidden = !any; list.hidden = !any;
    });
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-area") === area)); });
    empty.hidden = match > 0;
    var rest = match - shown;
    more.hidden = rest <= 0;
    if (rest > 0) more.textContent = "Mostra altri " + Math.min(PAGE, rest) + " di " + rest;
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function () { area = b.getAttribute("data-area"); shown = PAGE; apply(); });
  });
  input.addEventListener("input", function () { q = input.value; shown = PAGE; apply(); });
  more.addEventListener("click", function () { shown += PAGE; apply(); });
  document.getElementById("all-energy").addEventListener("click", function () {
    area = "Energia"; shown = PAGE; apply();
    document.getElementById("archivio").scrollIntoView({ behavior: "smooth" });
  });
  apply();
})();
