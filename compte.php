<?php
/**
 * Baracca - Site configurateur.baracca.fr
 * Espace client : profil et configurations enregistrées
 */
require_once __DIR__ . '/includes/auth.php';
require_once __DIR__ . '/includes/configurations.php';

// Page réservée aux comptes clients connectés
$user = archicad_current_user();
if ($user === null) {
    if (archicad_is_admin()) {
        // Session administrateur : pas de compte client -> direction le configurateur
        header('Location: configurateur.php');
        exit;
    }
    // Session active mais compte supprimé entre-temps : on nettoie la session
    archicad_logout();
    header('Location: connexion.php');
    exit;
}

$configs = archicad_user_configurations((string) $user['id']);

// ----- Actions du compte : modifier le profil, changer le mot de passe, supprimer une configuration -----
$message = null; // ['success'|'error', texte]
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!archicad_csrf_verify($_POST['csrf'] ?? null)) {
        $message = ['error', 'Jeton de sécurité invalide.'];
    } elseif (isset($_POST['suppr_config'])) {
        $cid = (string) ($_POST['config_id'] ?? '');
        $message = archicad_delete_configuration((string) $user['id'], $cid)
            ? ['success', 'Configuration supprimée.']
            : ['error', 'Configuration introuvable.'];
        $configs = archicad_user_configurations((string) $user['id']);
    } elseif (isset($_POST['maj_profil'])) {
        $fields = [];
        foreach (['nom', 'prenom', 'email', 'telephone', 'adresse_numero', 'adresse_rue', 'code_postal', 'ville', 'reference_cadastrale'] as $f) {
            $fields[$f] = trim((string) ($_POST[$f] ?? ''));
        }
        $updated = archicad_update_user((string) $user['id'], $fields);
        if ($updated === false) {
            $message = ['error', "Profil non enregistré : vérifiez les champs (email valide et non utilisé par un autre compte)."];
        } else {
            $user = $updated;
            $message = ['success', 'Profil mis à jour.'];
        }
    } elseif (isset($_POST['maj_password'])) {
        $current = (string) ($_POST['password_actuel'] ?? '');
        $new = (string) ($_POST['password'] ?? '');
        $confirm = (string) ($_POST['confirmation'] ?? '');
        if ($new !== $confirm) {
            $message = ['error', 'La confirmation du nouveau mot de passe ne correspond pas.'];
        } else {
            $res = archicad_change_user_password((string) $user['id'], $current, $new);
            $message = $res === true ? ['success', 'Mot de passe changé.'] : ['error', $res];
        }
    }
}

$pageTitle = 'Mon compte - Baracca';
$pageDescription = 'Votre espace client Baracca : profil et configurations de modules enregistrées.';
include 'includes/head.html';
?>

  <section class="section">
    <div class="container">
      <div class="auth-card auth-card-wide">
        <span class="section-tag">Espace client</span>
        <h1>Mon compte</h1>
        <p>Bienvenue<?= $user['prenom'] !== '' ? ', ' . htmlspecialchars($user['prenom']) : '' ?>. Retrouvez ici votre profil et vos configurations enregistrées dans le configurateur.</p>

        <?php if ($message !== null): ?>
          <div class="alert alert-<?= $message[0] === 'success' ? 'success' : 'error' ?>"><?= htmlspecialchars($message[1]) ?></div>
        <?php endif; ?>

        <table class="profile-table">
          <tbody>
            <tr><th>Membre depuis</th><td><?= htmlspecialchars($user['created']) ?></td></tr>
          </tbody>
        </table>

        <?php /* Zone modifiable : fond gris, champs empilés ; mot de passe dans le même fond, séparé par un trait fin */ ?>
        <div class="profile-edit">
        <form method="post" action="compte.php" class="auth-form">
          <input type="hidden" name="csrf" value="<?= htmlspecialchars(archicad_csrf_token()) ?>">
          <div class="auth-grid stack">
            <div class="form-group">
              <label for="nom">Nom <span class="required">*</span></label>
              <input type="text" id="nom" name="nom" required value="<?= htmlspecialchars((string) $user['nom']) ?>">
            </div>
            <div class="form-group">
              <label for="prenom">Prénom <span class="required">*</span></label>
              <input type="text" id="prenom" name="prenom" required value="<?= htmlspecialchars((string) $user['prenom']) ?>">
            </div>
            <div class="form-group">
              <label for="email">Email (identifiant de connexion) <span class="required">*</span></label>
              <input type="email" id="email" name="email" required value="<?= htmlspecialchars((string) $user['email']) ?>">
            </div>
            <div class="form-group">
              <label for="telephone">Téléphone</label>
              <input type="tel" id="telephone" name="telephone" value="<?= htmlspecialchars((string) ($user['telephone'] ?? '')) ?>" placeholder="06 12 34 56 78">
            </div>
            <div class="form-group">
              <label for="adresse_numero">Numéro</label>
              <input type="text" id="adresse_numero" name="adresse_numero" value="<?= htmlspecialchars((string) ($user['adresse_numero'] ?? '')) ?>" placeholder="12 bis">
            </div>
            <div class="form-group">
              <label for="adresse_rue">Rue</label>
              <input type="text" id="adresse_rue" name="adresse_rue" value="<?= htmlspecialchars((string) ($user['adresse_rue'] ?? '')) ?>" placeholder="Rue des Lilas">
            </div>
            <div class="form-group">
              <label for="code_postal">Code postal</label>
              <input type="text" id="code_postal" name="code_postal" inputmode="numeric" maxlength="5" value="<?= htmlspecialchars((string) ($user['code_postal'] ?? '')) ?>" placeholder="91300">
            </div>
            <div class="form-group">
              <label for="ville">Ville</label>
              <input type="text" id="ville" name="ville" value="<?= htmlspecialchars((string) ($user['ville'] ?? '')) ?>" placeholder="Massy">
            </div>
            <div class="form-group">
              <label for="reference_cadastrale">Référence cadastrale (facultative)</label>
              <input type="text" id="reference_cadastrale" name="reference_cadastrale" autocomplete="off" value="<?= htmlspecialchars((string) ($user['reference_cadastrale'] ?? '')) ?>" placeholder="Ex. section AB, parcelle 123">
            </div>
          </div>
          <div class="auth-actions">
            <button type="submit" name="maj_profil" value="1" class="btn btn-secondary">Enregistrer mon profil</button>
          </div>
        </form>
        <hr class="auth-separator">
        <form method="post" action="compte.php" class="auth-form">
          <input type="hidden" name="csrf" value="<?= htmlspecialchars(archicad_csrf_token()) ?>">
          <div class="auth-grid stack">
            <div class="form-group">
              <label for="password_actuel">Mot de passe actuel <span class="required">*</span></label>
              <input type="password" id="password_actuel" name="password_actuel" required autocomplete="current-password">
            </div>
            <div class="form-group">
              <label for="password">Nouveau mot de passe <span class="required">*</span></label>
              <input type="password" id="password" name="password" required minlength="8" autocomplete="new-password">
              <small class="form-hint">8 caractères minimum.</small>
            </div>
            <div class="form-group">
              <label for="confirmation">Confirmer le nouveau mot de passe <span class="required">*</span></label>
              <input type="password" id="confirmation" name="confirmation" required minlength="8" autocomplete="new-password">
            </div>
          </div>
          <div class="auth-actions">
            <button type="submit" name="maj_password" value="1" class="btn btn-secondary">Changer le mot de passe</button>
          </div>
        </form>
        </div>

        <h2>Mes configurations (<span id="configs-count"><?= count($configs) ?></span>)</h2>
        <div id="configs-msg" class="alert" style="display:none"></div>
        <p class="auth-links" id="configs-empty"<?= $configs === [] ? '' : ' style="display:none"' ?>>Aucune configuration enregistrée pour le moment. Lancez le <a href="configurateur.php">configurateur</a> et utilisez « Enregistrer cette configuration » dans l'onglet Export JSON.</p>
        <?php if ($configs !== []): ?>
          <table class="profile-table configs-table" id="configs-table">
            <thead>
              <tr><th>Configuration</th><th>Dernière modification</th></tr>
            </thead>
            <tbody>
              <?php foreach ($configs as $config): ?>
                <tr data-config-id="<?= htmlspecialchars((string) $config['id']) ?>">
                  <td>
                    <div class="config-line">
                      <strong><?= htmlspecialchars((string) $config['nom']) ?></strong>
                      <a href="configurateur.php?config=<?= urlencode((string) $config['id']) ?>" class="btn btn-charger btn-small">Charger</a>
                      <button type="button" class="btn btn-danger btn-suppr btn-small btn-suppr-config" data-id="<?= htmlspecialchars((string) $config['id']) ?>" title="Supprimer" aria-label="Supprimer cette configuration">
                        <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><path d="M3.5 3.5l9 9m0-9l-9 9" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/></svg>
                      </button>
                    </div>
                  </td>
                  <td><?= htmlspecialchars((string) $config['updated']) ?></td>
                </tr>
              <?php endforeach; ?>
            </tbody>
          </table>
        <?php endif; ?>
      </div>
    </div>
  </section>

  <script>
    // Suppression d'une configuration sans rechargement de page (API JSON,
    // comme dans le configurateur) : la ligne disparaît et le compteur est mis à jour
    document.addEventListener('DOMContentLoaded', function () {
      var msg = document.getElementById('configs-msg');
      var countEl = document.getElementById('configs-count');
      var table = document.getElementById('configs-table');
      var emptyP = document.getElementById('configs-empty');
      var showMsg = function (cls, text) {
        if (!msg) return;
        msg.className = 'alert ' + cls;
        msg.textContent = text;
        msg.style.display = '';
      };
      document.querySelectorAll('.btn-suppr-config').forEach(function (btn) {
        btn.addEventListener('click', async function () {
          var id = btn.getAttribute('data-id');
          btn.disabled = true;
          try {
            var r = await fetch('php/api_configurations.php', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action: 'delete', id: id })
            });
            var g = await r.json();
            if (g.ok) {
              var sel = 'tr[data-config-id="' + (window.CSS && CSS.escape ? CSS.escape(id) : id) + '"]';
              var row = table ? table.querySelector(sel) : null;
              if (row) row.remove();
              if (countEl) countEl.textContent = String(Math.max(0, (parseInt(countEl.textContent, 10) || 0) - 1));
              if (table && !table.querySelector('tbody tr')) {
                table.style.display = 'none';
                if (emptyP) emptyP.style.display = '';
              }
              showMsg('alert-success', 'Configuration supprimée.');
            } else {
              showMsg('alert-error', g.error || 'Suppression impossible.');
              btn.disabled = false;
            }
          } catch (e) {
            showMsg('alert-error', 'Suppression impossible.');
            btn.disabled = false;
          }
        });
      });
    });
  </script>

<?php include 'includes/footer.php'; ?>
