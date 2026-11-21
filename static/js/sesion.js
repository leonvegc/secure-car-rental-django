// UTN-07c (lado del navegador): avisa y redirige al login cuando se cumplen los
// segundos de inactividad. La expiración REAL la hace el servidor; este script
// solo evita que el usuario vea una página vieja. No usa innerHTML (UTN-07b).
(function () {
  "use strict";
  var cuerpo = document.body;
  var segundos = parseInt(cuerpo.getAttribute("data-sesion-segundos"), 10);
  var urlLogin = cuerpo.getAttribute("data-url-login");
  if (!segundos || !urlLogin) { return; }

  var aviso = document.getElementById("aviso-sesion");
  var contador = document.getElementById("aviso-sesion-segundos");
  var inicio = Date.now();

  setInterval(function () {
    var restantes = segundos - Math.floor((Date.now() - inicio) / 1000);
    if (restantes <= 15 && aviso && contador) {
      aviso.classList.remove("oculto");
      contador.textContent = String(Math.max(restantes, 0));
    }
    if (restantes <= -2) { // margen para que el servidor ya haya vencido la sesión
      window.location.assign(urlLogin + "?expirada=1");
    }
  }, 1000);
})();
