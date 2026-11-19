<?php
/**
 * Baracca - Back-office (configurateur.baracca.fr)
 * Gestion des comptes « staff » : vendeurs et partenaires (data/users.json,
 * role = vendeur|partenaire). Comme un client, ils ont accès au configurateur
 * en ligne ; côté back-office, ils n'accèdent qu'aux rubriques cochées dans
 * leur fiche (arborescence des accès ci-dessous).
 *
 * ?role=vendeur|partenaire  — liste + fiche + ajout/édition/suppression
 */

require_once __DIR__ . '/../includes/admin-auth.php';
require_once __DIR__ . '/../includes/users.php';
require_once __DIR__ . '/../includes/configurations.php';
require_once __DIR__ . '/../includes/acces.php';

$role = (string) ($_GET['role'] ?? 'vendeur');
if (!in_array($role, archicad_bo_roles(), true)) {
    $role = 'vendeur';
}
$tabKey = $role === 'vendeur' ? 'vendeurs' : 'partenaires';
$roleLabel = $role === 'vendeur' ? 'Vendeurs' : 'Partenaires';
$roleSing = $role === 'vendeur' ? 'vendeur' : 'partenaire';

archicad_bo_require($tabKey);

$profilFields = ['nom', 'prenom', 'societe', 'email', 'telephone', 'adresse_numero', 'adresse_rue', 'code_postal', 'ville', 'reference_cadastrale'];

$message = null; // ['success'|'error', texte]
$id = (string) ($_GET['id'] ?? '');
$new = isset($_GET['new']);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!archicad_admin_csrf_verify($_POST['csrf'] ?? null)) {
        $message = ['error', 'Jeton de sécurité invalide.'];
    } elseif (isset($_POST['ajouter'])) {
        $fields = [];
        foreach ($profilFields as $f) {
            $fields[$f] = trim((string) ($_POST[$f] ?? ''));
        }
        $password = (string) ($_POST['password'] ?? '');
        $confirmation = (string) ($_POST['confirmation'] ?? '');
        $acces = array_map('strval', (array) ($_POST['acces'] ?? []));
        if ($fields['email'] === '' || !filter_var($fields['email'], FILTER_VALIDATE_EMAIL)) {
            $message = ['error', "L'email est obligatoire et doit être valide."];
        } elseif (strlen($password) < 8) {
            $message = ['error', 'Le mot de passe doit contenir au moins 8 caractères.'];
        } elseif ($password !== $confirmation) {
            $message = ['error', 'La confirmation du mot de passe ne correspond pas.'];
        } elseif (archicad_find_user_by_email($fields['email']) !== null) {
            $message = ['error', 'Un compte existe déjà avec cet email.'];
        } else {
            $created = archicad_add_staff($fields, $password, $role, $acces);
            if ($created !== false) {
                header('Location: staff.php?role=' . urlencode($role) . '&id=' . urlencode((string) $created['id']) . '&success=created');
                exit;
            }
            $message = ['error', "Impossible de créer le compte $roleSing."];
        }
    } elseif (isset($_POST['maj'])) {
        $fields = [];
        foreach ($profilFields as $f) {
            $fields[$f] = trim((string) ($_POST[$f] ?? ''));
        }
        $acces = array_map('strval', (array) ($_POST['acces'] ?? []));
        $updated = archicad_update_staff($id, $fields, $role, $acces);
        if ($updated === false) {
            $message = ['error', "Informations non enregistrées : email invalide ou déjà utilisé par un autre compte."];
        } else {
            $message = ['success', 'Fiche mise à jour (profil + accès).'];
            $id = (string) $updated['id'];
        }
    } elseif (isset($_POST['reinit'])) {
        $password = (string) ($_POST['password'] ?? '');
        $confirmation = (string) ($_POST['confirmation'] ?? '');
        if (strlen($password) < 8) {
            $message = ['error', 'Le mot de passe doit contenir au moins 8 caractères.'];
        } elseif ($password !== $confirmation) {
            $message = ['error', 'La confirmation du mot de passe ne correspond pas.'];
        } else {
            $message = archicad_set_user_password($id, $password)
                ? ['success', 'Mot de passe réinitialisé.']
                : ['error', 'Compte introuvable.'];
        }
    } elseif (isset($_POST['supprimer'])) {
        archicad_delete_user_configurations($id);
        archicad_delete_user($id);
        header('Location: staff.php?role=' . urlencode($role) . '&success=deleted');
        exit;
    }
}

$staff = archicad_users_by_role($role);
$fiche = null;
if ($id !== '') {
    $fiche = archicad_find_user_by_id($id);
    if ($fiche === null || archicad_user_role($fiche) !== $role) {
        header('Location: staff.php?role=' . urlencode($role));
        exit;
    }
}
$success = (string) ($_GET['success'] ?? '');

// Résumé des accès cochés (labels des nœuds de premier niveau)
function staff_acces_resume(array $acces): string
{
    $labels = [];
    foreach (archicad_acces_tree() as $n) {
        if (in_array((string) $n['key'], $acces, true)) {
            $labels[] = (string) $n['label'];
        }
    }
    return $labels !== [] ? implode(', ', $labels) : '—';
}

// Résumé de la zone géographique (noms des départements attribués)
function staff_deps_resume(array $deps): string
{
    $map = archicad_departements();
    $labels = [];
    foreach ($deps as $d) {
        $d = (string) $d;
        $labels[] = isset($map[$d]) ? $map[$d][2] . ' (' . $d . ')' : $d;
    }
    return $labels !== [] ? implode(', ', $labels) : 'toute la France';
}

$pageTitle = $roleLabel;
$adminPage = 'comptes';
include __DIR__ . '/../includes/admin-head.php';
?>
    <div class="admin-card">
      <h1>Gestion des comptes</h1>
      <?php archicad_comptes_tabs($tabKey); ?>
      <p>Les <?= strtolower($roleLabel) ?> disposent du configurateur en ligne (comme les clients) et, côté back-office, des seules rubriques cochées ci-dessous dans leur fiche.</p>
      <?php if ($message !== null): ?>
        <p class="admin-message admin-message-<?= $message[0] ?>"><?= htmlspecialchars($message[1]) ?></p>
      <?php endif; ?>
      <?php if ($success === 'created'): ?>
        <p class="admin-message admin-message-success">Compte <?= htmlspecialchars($roleSing) ?> créé.</p>
      <?php endif; ?>
      <?php if ($success === 'deleted'): ?>
        <p class="admin-message admin-message-success">Compte supprimé, ainsi que ses configurations enregistrées.</p>
      <?php endif; ?>
    </div>

<?php if ($fiche !== null): // ----- fiche d'un compte staff ----- ?>
    <?php $accesFiche = array_map('strval', (array) ($fiche['acces'] ?? [])); ?>
    <div class="admin-card">
      <h2><?= htmlspecialchars(trim((string) ($fiche['prenom'] ?? '') . ' ' . (string) ($fiche['nom'] ?? ''))) ?> <span class="admin-hint">(<?= htmlspecialchars($roleSing) ?> — <?= htmlspecialchars((string) ($fiche['email'] ?? '')) ?>)</span></h2>
      <p><a href="staff.php?role=<?= urlencode($role) ?>">← Retour à la liste des <?= strtolower($roleLabel) ?></a></p>
      <table class="admin-table">
        <tbody>
          <tr><th>Société</th><td><?= ($fiche['societe'] ?? '') !== '' ? htmlspecialchars((string) $fiche['societe']) : '—' ?></td></tr>
          <tr><th>Accès back-office</th><td><?= htmlspecialchars(staff_acces_resume($accesFiche)) ?></td></tr>
          <tr><th>Zone géographique</th><td><?= htmlspecialchars(staff_deps_resume(array_map('strval', (array) ($fiche['departements'] ?? [])))) ?></td></tr>
          <tr><th>Configurations enregistrées</th><td><?= archicad_count_configurations((string) ($fiche['id'] ?? '')) ?></td></tr>
          <tr><th>Dernière connexion</th><td><?= ($fiche['last_login'] ?? '') !== '' ? htmlspecialchars((string) $fiche['last_login']) : 'jamais' ?></td></tr>
          <tr><th>Inscrit le</th><td><?= htmlspecialchars((string) ($fiche['created'] ?? '')) ?></td></tr>
        </tbody>
      </table>
    </div>
    <div class="admin-card">
      <h2>Modifier le profil et les accès</h2>
      <form method="post" action="staff.php?role=<?= urlencode($role) ?>&id=<?= urlencode($id) ?>" class="admin-form">
        <input type="hidden" name="csrf" value="<?= htmlspecialchars(archicad_admin_csrf_token()) ?>">
        <div class="modal-row stack">
          <div class="admin-form-row"><label for="nom">Nom</label><input type="text" id="nom" name="nom" required value="<?= htmlspecialchars((string) ($fiche['nom'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="prenom">Prénom</label><input type="text" id="prenom" name="prenom" value="<?= htmlspecialchars((string) ($fiche['prenom'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="societe">Société</label><input type="text" id="societe" name="societe" value="<?= htmlspecialchars((string) ($fiche['societe'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="email">Email (identifiant de connexion)</label><input type="email" id="email" name="email" required value="<?= htmlspecialchars((string) ($fiche['email'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="telephone">Téléphone</label><input type="text" id="telephone" name="telephone" value="<?= htmlspecialchars((string) ($fiche['telephone'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="adresse_numero">N°</label><input type="text" id="adresse_numero" name="adresse_numero" value="<?= htmlspecialchars((string) ($fiche['adresse_numero'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="adresse_rue">Rue</label><input type="text" id="adresse_rue" name="adresse_rue" value="<?= htmlspecialchars((string) ($fiche['adresse_rue'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="code_postal">Code postal</label><input type="text" id="code_postal" name="code_postal" value="<?= htmlspecialchars((string) ($fiche['code_postal'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="ville">Ville</label><input type="text" id="ville" name="ville" value="<?= htmlspecialchars((string) ($fiche['ville'] ?? '')) ?>"></div>
          <div class="admin-form-row"><label for="reference_cadastrale">Réf. cadastrale</label><input type="text" id="reference_cadastrale" name="reference_cadastrale" value="<?= htmlspecialchars((string) ($fiche['reference_cadastrale'] ?? '')) ?>"></div>
        </div>
        <fieldset class="admin-acces">
          <legend>Accès au back-office (arborescence du site)</legend>
          <p class="admin-hint">Cocher un nœud autorise toutes ses sous-rubriques. Le configurateur en ligne reste accessible dans tous les cas.</p>
          <?php foreach (archicad_acces_tree() as $n): ?>
            <?php archicad_acces_checkbox($n, $accesFiche); ?>
          <?php endforeach; ?>
        </fieldset>
        <fieldset class="admin-acces">
          <legend>Zone géographique (départements attribués)</legend>
          <p class="admin-hint">Cliquez sur la carte pour attribuer des départements : ce <?= htmlspecialchars($roleSing) ?> ne verra que les clients et soumissions dont le code postal est dans sa zone. Aucune sélection = toute la France.</p>
          <?php archicad_departements_carte(array_map('strval', (array) ($fiche['departements'] ?? []))); ?>
        </fieldset>
        <button type="submit" name="maj" value="1" class="btn btn-cta">Enregistrer</button>
      </form>
    </div>
    <div class="admin-card">
      <h2>Mot de passe</h2>
      <form method="post" action="staff.php?role=<?= urlencode($role) ?>&id=<?= urlencode($id) ?>" class="admin-form-inline">
        <input type="hidden" name="csrf" value="<?= htmlspecialchars(archicad_admin_csrf_token()) ?>">
        <input type="password" name="password" required minlength="8" autocomplete="new-password" placeholder="Nouveau mot de passe (8 car. min.)" style="width:220px">
        <input type="password" name="confirmation" required minlength="8" autocomplete="new-password" placeholder="Confirmation" style="width:160px">
        <button type="submit" name="reinit" value="1" class="btn btn-secondary btn-small">Changer le mot de passe</button>
      </form>
    </div>
    <div class="admin-card">
      <h2>Supprimer le compte</h2>
      <form method="post" action="staff.php?role=<?= urlencode($role) ?>&id=<?= urlencode($id) ?>" onsubmit="return confirm('Supprimer ce compte et ses configurations enregistrées ?');">
        <input type="hidden" name="csrf" value="<?= htmlspecialchars(archicad_admin_csrf_token()) ?>">
        <button type="submit" name="supprimer" value="1" class="btn-danger btn-small">Supprimer le compte</button>
      </form>
    </div>

<?php elseif ($new): // ----- formulaire de création ----- ?>
    <div class="admin-card">
      <h2>Ajouter un <?= htmlspecialchars($roleSing) ?></h2>
      <form method="post" action="staff.php?role=<?= urlencode($role) ?>&new=1" class="admin-form">
        <input type="hidden" name="csrf" value="<?= htmlspecialchars(archicad_admin_csrf_token()) ?>">
        <div class="modal-row stack">
          <div class="admin-form-row"><label for="nom">Nom</label><input type="text" id="nom" name="nom" required></div>
          <div class="admin-form-row"><label for="prenom">Prénom</label><input type="text" id="prenom" name="prenom"></div>
          <div class="admin-form-row"><label for="societe">Société</label><input type="text" id="societe" name="societe"></div>
          <div class="admin-form-row"><label for="email">Email (identifiant de connexion)</label><input type="email" id="email" name="email" required></div>
          <div class="admin-form-row"><label for="telephone">Téléphone</label><input type="text" id="telephone" name="telephone"></div>
          <div class="admin-form-row"><label for="adresse_numero">N°</label><input type="text" id="adresse_numero" name="adresse_numero"></div>
          <div class="admin-form-row"><label for="adresse_rue">Rue</label><input type="text" id="adresse_rue" name="adresse_rue"></div>
          <div class="admin-form-row"><label for="code_postal">Code postal</label><input type="text" id="code_postal" name="code_postal"></div>
          <div class="admin-form-row"><label for="ville">Ville</label><input type="text" id="ville" name="ville"></div>
          <div class="admin-form-row"><label for="reference_cadastrale">Réf. cadastrale</label><input type="text" id="reference_cadastrale" name="reference_cadastrale"></div>
          <div class="admin-form-row"><label for="password">Mot de passe</label><input type="password" id="password" name="password" required minlength="8" autocomplete="new-password" placeholder="8 caractères minimum"></div>
          <div class="admin-form-row"><label for="confirmation">Confirmation</label><input type="password" id="confirmation" name="confirmation" required minlength="8" autocomplete="new-password"></div>
        </div>
        <fieldset class="admin-acces">
          <legend>Accès au back-office (arborescence du site)</legend>
          <p class="admin-hint">Cocher un nœud autorise toutes ses sous-rubriques. Le configurateur en ligne reste accessible dans tous les cas.</p>
          <?php foreach (archicad_acces_tree() as $n): ?>
            <?php archicad_acces_checkbox($n, []); ?>
          <?php endforeach; ?>
        </fieldset>
        <fieldset class="admin-acces">
          <legend>Zone géographique (départements attribués)</legend>
          <p class="admin-hint">Cliquez sur la carte pour attribuer des départements : ce <?= htmlspecialchars($roleSing) ?> ne verra que les clients et soumissions dont le code postal est dans sa zone. Aucune sélection = toute la France.</p>
          <?php archicad_departements_carte([]); ?>
        </fieldset>
        <button type="submit" name="ajouter" value="1" class="btn btn-cta">Créer le <?= htmlspecialchars($roleSing) ?></button>
      </form>
    </div>

<?php else: // ----- liste des comptes du rôle ----- ?>
    <div class="admin-card">
      <h2><?= $roleLabel ?> (<?= count($staff) ?>) <a class="btn-add" href="staff.php?role=<?= urlencode($role) ?>&new=1" title="Ajouter un <?= htmlspecialchars($roleSing) ?>">+</a></h2>
      <?php if ($staff === []): ?>
        <p class="admin-hint">Aucun compte <?= htmlspecialchars($roleSing) ?> pour le moment.</p>
      <?php else: ?>
        <table class="admin-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Société</th>
              <th>Email</th>
              <th>Zone géographique</th>
              <th>Accès back-office</th>
              <th>Dernière connexion</th>
              <th>Créé le</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ($staff as $u): ?>
              <tr>
                <td><strong><a href="staff.php?role=<?= urlencode($role) ?>&id=<?= urlencode((string) ($u['id'] ?? '')) ?>"><?= htmlspecialchars(trim((string) ($u['prenom'] ?? '') . ' ' . (string) ($u['nom'] ?? ''))) ?></a></strong></td>
                <td><?= ($u['societe'] ?? '') !== '' ? htmlspecialchars((string) $u['societe']) : '—' ?></td>
                <td><?= htmlspecialchars((string) ($u['email'] ?? '')) ?></td>
                <td><?= htmlspecialchars(staff_deps_resume(array_map('strval', (array) ($u['departements'] ?? [])))) ?></td>
                <td><?= htmlspecialchars(staff_acces_resume(array_map('strval', (array) ($u['acces'] ?? [])))) ?></td>
                <td><?= ($u['last_login'] ?? '') !== '' ? htmlspecialchars((string) $u['last_login']) : '—' ?></td>
                <td><?= htmlspecialchars((string) ($u['created'] ?? '')) ?></td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      <?php endif; ?>
    </div>
<?php endif; ?>
<?php
include __DIR__ . '/../includes/admin-footer.php';
