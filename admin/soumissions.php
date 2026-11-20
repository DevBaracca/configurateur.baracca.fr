<?php
/**
 * Baracca - Back-office (configurateur.baracca.fr)
 * Configurations soumises à Baracca via le bouton « Soumettre » du configurateur
 */

require_once __DIR__ . '/../includes/admin-auth.php';
require_once __DIR__ . '/../includes/soumissions.php';
require_once __DIR__ . '/../includes/acces.php';

archicad_bo_require('soumissions');

$message = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['supprimer'])) {
    if (!archicad_admin_csrf_verify($_POST['csrf'] ?? null)) {
        $message = ['error', 'Jeton de sécurité invalide.'];
    } else {
        $message = archicad_delete_soumission((string) ($_POST['fichier'] ?? ''))
            ? ['success', 'Soumission supprimée.']
            : ['error', 'Soumission introuvable.'];
    }
}

$soumissions = archicad_bo_filter_soumissions(archicad_load_soumissions()); // filtrées par zone si vendeur/partenaire
$pageTitle = 'Soumissions';
$adminPage = 'soumissions';
include __DIR__ . '/../includes/admin-head.php';
?>
    <div class="admin-card">
      <h1>Soumissions</h1>
      <p>Configurations envoyées à Baracca par les clients via le bouton « Soumettre » du configurateur. Le fichier JSON téléchargé est le format d'échange consommé par les scripts Python côté Archicad.</p>
      <?php if ($message !== ''): ?>
        <p class="admin-message admin-message-<?= $message[0] ?>"><?= htmlspecialchars($message[1]) ?></p>
      <?php endif; ?>
    </div>
    <div class="admin-card">
      <h2>Configurations soumises (<span id="soumissions-count"><?= count($soumissions) ?></span>)</h2>
      <div id="soumissions-msg" class="admin-message" style="display:none"></div>
      <p class="admin-hint" id="soumissions-empty"<?= $soumissions === [] ? '' : ' style="display:none"' ?>>Aucune soumission pour le moment.</p>
      <?php if ($soumissions !== []): ?>
        <table class="admin-table" id="soumissions-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Module</th>
              <th>Surface plancher</th>
              <th>Client</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ($soumissions as $soumission): ?>
              <tr data-fichier="<?= htmlspecialchars($soumission['fichier']) ?>">
                <td><?= htmlspecialchars($soumission['soumis_le']) ?></td>
                <td><strong><?= htmlspecialchars($soumission['module']) ?></strong></td>
                <td><?= htmlspecialchars($soumission['surface']) ?> m²</td>
                <td>
                  <?php if ($soumission['utilisateur'] !== null): ?>
                    <strong><?= htmlspecialchars(trim(($soumission['utilisateur']['prenom'] ?? '') . ' ' . ($soumission['utilisateur']['nom'] ?? ''))) ?></strong>
                    <div class="admin-sub"><?= htmlspecialchars((string) ($soumission['utilisateur']['email'] ?? '')) ?></div>
                  <?php else: ?>
                    <span class="admin-sub">—</span>
                  <?php endif; ?>
                </td>
                <td>
                  <div class="admin-actions">
                    <a href="soumission.php?fichier=<?= urlencode($soumission['fichier']) ?>" class="icon-btn" title="Télécharger le JSON" aria-label="Télécharger le JSON">
                      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12m0 0l-4-4m4 4l4-4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>
                    </a>
                    <form method="post" action="soumissions.php" class="admin-inline-form form-suppr-soumission"
                          data-fichier="<?= htmlspecialchars($soumission['fichier']) ?>"
                          data-module="<?= htmlspecialchars($soumission['module']) ?>"
                          data-date="<?= htmlspecialchars($soumission['soumis_le']) ?>"
                          onsubmit="return window.onSubmitSuppr ? onSubmitSuppr(this) : confirm('Supprimer définitivement cette soumission ?');">
                      <input type="hidden" name="csrf" value="<?= htmlspecialchars(archicad_admin_csrf_token()) ?>">
                      <input type="hidden" name="fichier" value="<?= htmlspecialchars($soumission['fichier']) ?>">
                      <button type="submit" name="supprimer" value="1" class="icon-btn danger btn-suppr-soumission" title="Supprimer" aria-label="Supprimer">
                        <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><path d="M3.5 3.5l9 9m0-9l-9 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/></svg>
                      </button>
                    </form>
                  </div>
                </td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      <?php endif; ?>
    </div>
    <div class="modal-backdrop" id="modal-suppr-soumission" style="display:none" onclick="if(event.target===this)fermerModalSuppr()">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-suppr-titre">
        <button type="button" class="modal-close" onclick="fermerModalSuppr()" title="Fermer" aria-label="Fermer">
          <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3.5 3.5l9 9m0-9l-9 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/></svg>
        </button>
        <div class="admin-card">
          <h2 id="modal-suppr-titre">Supprimer cette soumission ?</h2>
          <p id="modal-suppr-texte" class="admin-hint"></p>
          <div class="admin-actions">
            <button type="button" class="btn" onclick="fermerModalSuppr()">Annuler</button>
            <button type="button" class="btn btn-danger" id="modal-suppr-valider">Supprimer</button>
          </div>
        </div>
      </div>
    </div>
    <script>
    // Suppression dynamique (sans rechargement), comme « Mon compte » : un clic
    // sur supprimer ouvre d'abord la modale de confirmation, puis appelle
    // l'API ../php/api_soumissions.php ; la ligne disparaît et le compteur est
    // mis à jour. Sans JS, le formulaire POST reste fonctionnel (repli).
    (function () {
      var CSRF = <?= json_encode(archicad_admin_csrf_token()) ?>;
      var API = '../php/api_soumissions.php';
      var modal = document.getElementById('modal-suppr-soumission');
      var texte = document.getElementById('modal-suppr-texte');
      var btnValider = document.getElementById('modal-suppr-valider');
      var msg = document.getElementById('soumissions-msg');
      var countEl = document.getElementById('soumissions-count');
      var table = document.getElementById('soumissions-table');
      var emptyP = document.getElementById('soumissions-empty');
      var courant = null; // { fichier, module, date }

      function showMsg(cls, text) {
        if (!msg) return;
        msg.className = 'admin-message ' + cls;
        msg.textContent = text;
        msg.style.display = '';
      }
      function esc(s) {
        return (window.CSS && CSS.escape) ? CSS.escape(s) : s;
      }
      window.fermerModalSuppr = function () {
        if (modal) modal.style.display = 'none';
        courant = null;
      };
      window.onSubmitSuppr = function (form) {
        courant = {
          fichier: form.getAttribute('data-fichier') || '',
          module: form.getAttribute('data-module') || '',
          date: form.getAttribute('data-date') || ''
        };
        if (texte) {
          texte.textContent = 'Soumission « ' + courant.module + ' » du ' + courant.date +
            ' — supprimer définitivement le fichier JSON correspondant ?';
        }
        if (modal) modal.style.display = 'flex';
        return false; // le POST n'est utilisé qu'en repli sans JS
      };
      if (btnValider) {
        btnValider.addEventListener('click', async function () {
          if (!courant) return;
          btnValider.disabled = true;
          try {
            var r = await fetch(API, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action: 'delete', fichier: courant.fichier, csrf: CSRF })
            });
            var g = await r.json();
            if (g.ok) {
              var row = table ? table.querySelector('tr[data-fichier="' + esc(courant.fichier) + '"]') : null;
              if (row) row.remove();
              if (countEl) countEl.textContent = String(Math.max(0, (parseInt(countEl.textContent, 10) || 0) - 1));
              if (table && !table.querySelector('tbody tr')) {
                table.style.display = 'none';
                if (emptyP) emptyP.style.display = '';
              }
              showMsg('admin-message-success', 'Soumission supprimée.');
            } else {
              showMsg('admin-message-error', g.error || 'Suppression impossible.');
            }
          } catch (e) {
            showMsg('admin-message-error', 'Suppression impossible.');
          }
          window.fermerModalSuppr();
          btnValider.disabled = false;
        });
      }
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') window.fermerModalSuppr();
      });
    })();
    </script>
<?php
include __DIR__ . '/../includes/admin-footer.php';
