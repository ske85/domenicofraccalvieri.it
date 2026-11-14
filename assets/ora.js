/* Data e ora correnti accanto al nome, come la riga della data in testata. Si aggiorna da sola ogni minuto. */
(function () {
  var el = document.getElementById("adesso");
  if (!el) return;
  function tick() {
    var d = new Date();
    var data = d.toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    var ora = d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
    el.textContent = data + " · ore " + ora;
    el.setAttribute("datetime", d.toISOString());
    el.hidden = false;
    setTimeout(tick, (60 - d.getSeconds()) * 1000 + 50);
  }
  tick();
})();
