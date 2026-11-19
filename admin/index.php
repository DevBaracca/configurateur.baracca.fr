<?php
/**
 * Baracca - Back-office (configurateur.baracca.fr)
 * Connexion administrateur + tableau de bord
 */

require_once __DIR__ . '/../includes/admin-auth.php';
require_once __DIR__ . '/../includes/users.php';
require_once __DIR__ . '/../includes/configurations.php';
require_once __DIR__ . '/../includes/soumissions.php';
require_once __DIR__ . '/../includes/stats.php';
require_once __DIR__ . '/../includes/acces.php';

$loginError = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['username'], $_POST['password'])) {
    if (archicad_admin_rate_limit_is_blocked()) {
        $minutes = (int) ceil(archicad_admin_rate_limit_blocked_seconds() / 60);
        $loginError = 'Trop de tentatives de connexion. Réessayez dans ' . $minutes . ' min.';
    } elseif (archicad_bo_login((string) $_POST['username'], (string) $_POST['password'])) {
        archicad_admin_rate_limit_success();
        header('Location: index.php');
        exit;
    } else {
        archicad_admin_rate_limit_failure();
        $loginError = 'Identifiants incorrects.';
    }
}

if (!archicad_bo_is_logged_in()) {
    $pageTitle = 'Connexion';
    include __DIR__ . '/../includes/admin-head.php';
    ?>
    <div class="admin-card admin-login">
      <h1>Administration Baracca</h1>
      <p class="admin-hint">Back-office du site configurateur.baracca.fr — administrateur (identifiant), vendeur ou partenaire (email).</p>
      <?php if ($loginError !== ''): ?>
        <p class="admin-message admin-message-error"><?= htmlspecialchars($loginError) ?></p>
      <?php endif; ?>
      <form method="post" action="index.php">
        <div class="admin-form-row">
          <label for="username">Identifiant ou email</label>
          <input type="text" id="username" name="username" required autofocus autocomplete="username">
        </div>
        <div class="admin-form-row">
          <label for="password">Mot de passe</label>
          <div class="password-field">
            <input type="password" id="password" name="password" required autocomplete="current-password">
            <button type="button" class="password-toggle" id="password-toggle" aria-label="Afficher le mot de passe" title="Afficher / masquer le mot de passe">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
                <line class="eye-slash" x1="4" y1="4" x2="20" y2="20"></line>
              </svg>
            </button>
          </div>
        </div>
        <button type="submit" class="btn btn-cta">Se connecter</button>
      </form>
    </div>
    <script>
      // Bascule afficher/masquer le mot de passe (icône œil)
      (function () {
        var btn = document.getElementById('password-toggle');
        var input = document.getElementById('password');
        if (!btn || !input) return;
        btn.addEventListener('click', function () {
          var show = input.type === 'password';
          input.type = show ? 'text' : 'password';
          btn.classList.toggle('visible', show);
          btn.setAttribute('aria-label', show ? 'Masquer le mot de passe' : 'Afficher le mot de passe');
          btn.title = show ? 'Masquer le mot de passe' : 'Afficher le mot de passe';
        });
      })();
    </script>
    <?php
    include __DIR__ . '/../includes/admin-footer.php';
    exit;
}

archicad_bo_require('index');
$stats = archicad_stats_collect(); // métriques multi-sites (compteurs des onglets)
// Onglets du tableau de bord : un onglet par site baracca.fr
$tabsSites = ['configurateur' => 'Configurateur', 'invest' => 'Invest', 'blog' => 'Blog'];
$siteTab = (string) ($_GET['site'] ?? 'configurateur');
if (!isset($tabsSites[$siteTab])) {
    $siteTab = 'configurateur';
}
$pageTitle = 'Tableau de bord';
$adminPage = 'index';
include __DIR__ . '/../includes/admin-head.php';
?>
    <div class="admin-card">
      <h1>Tableau de bord</h1>
      <p>Gérez les comptes clients du configurateur et consultez les configurations soumises, depuis cette interface.</p>
      <nav class="admin-tabs admin-subtabs">
        <?php foreach ($tabsSites as $key => $label): ?>
          <a href="index.php?site=<?= $key ?>"<?= $siteTab === $key ? ' class="active"' : '' ?>><?= $label ?> (<?= (int) ($stats['sites'][$key]['total'] ?? 0) ?>)</a>
        <?php endforeach; ?>
      </nav>
    </div>
<?php if ($siteTab === 'configurateur'): ?>
    <div class="admin-grid">
      <?php if (archicad_bo_can('utilisateurs') || archicad_bo_can('vendeurs') || archicad_bo_can('partenaires')): ?>
      <div class="admin-card admin-dash-card">
        <div class="admin-dash-head">
          <h2><a href="comptes.php" class="admin-dash-link">Gestion des comptes <span class="admin-dash-count"><?= archicad_users_count() ?></span></a></h2>
          <p class="admin-dash-desc">Comptes ayant accès au configurateur : clients inscrits en ligne, vendeurs, partenaires (profil complet : identité, adresse, référence cadastrale).</p>
        </div>
      </div>
      <?php endif; ?>
      <?php if (archicad_bo_can('soumissions')): ?>
      <div class="admin-card admin-dash-card">
        <div class="admin-dash-head">
          <h2><a href="soumissions.php" class="admin-dash-link">Soumissions <span class="admin-dash-count"><?= archicad_soumissions_count() ?></span></a></h2>
          <p class="admin-dash-desc">Configurations envoyées à Baracca via le bouton « Soumettre » du configurateur.</p>
        </div>
      </div>
      <?php endif; ?>
      <div class="admin-card admin-dash-card">
        <div class="admin-dash-head">
          <h2><a href="../configurateur.php" target="_blank" class="admin-dash-link">Configurations enregistrées <span class="admin-dash-count"><?= archicad_configurations_total() ?></span></a></h2>
          <p class="admin-dash-desc">Configurations enregistrées par les clients dans leur espace (onglet « Export JSON » du configurateur). Elles restent la propriété de chaque client.</p>
        </div>
      </div>
      <?php if (archicad_bo_can('administrateurs')): ?>
      <div class="admin-card admin-dash-card">
        <div class="admin-dash-head">
          <h2><a href="administrateurs.php" class="admin-dash-link">Administrateurs <span class="admin-dash-count"><?= count(archicad_load_admins()) ?></span></a></h2>
          <p class="admin-dash-desc">Comptes administrateurs du back-office (ajout, changement de mot de passe, suppression du dernier excepté). Le compte initial vient de <code>config.php</code>.</p>
        </div>
      </div>
      <?php endif; ?>
    </div>
<?php
// Statistiques d'utilisation du configurateur (graphiques) sous les cartes
include __DIR__ . '/../includes/admin-stats.php';
else:
// Onglet invest / blog : métriques de ce site, remontées au collecteur central
include __DIR__ . '/../includes/admin-site-stats.php';
endif;
include __DIR__ . '/../includes/admin-footer.php';
