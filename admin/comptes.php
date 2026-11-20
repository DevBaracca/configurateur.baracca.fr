<?php
/**
 * Baracca - Back-office (configurateur.baracca.fr)
 * Rubrique « Gestion des comptes » : redirige vers l'onglet demandé
 * (utilisateurs / vendeurs / partenaires / administrateurs).
 */

require_once __DIR__ . '/../includes/admin-auth.php';
require_once __DIR__ . '/../includes/acces.php';

// Accessible si la rubrique elle-même ou l'un de ses onglets est autorisé
archicad_bo_require_any(['comptes', 'utilisateurs', 'vendeurs', 'partenaires', 'administrateurs']);

$tab = (string) ($_GET['tab'] ?? '');
$map = [
    'utilisateurs' => ['utilisateurs.php', 'utilisateurs'],
    'vendeurs' => ['staff.php?role=vendeur', 'vendeurs'],
    'partenaires' => ['staff.php?role=partenaire', 'partenaires'],
    'administrateurs' => ['administrateurs.php', 'administrateurs'],
];
// Onglet demandé autorisé ? sinon premier onglet autorisé
if (!isset($map[$tab]) || !archicad_bo_can($map[$tab][1])) {
    $tab = '';
    foreach ($map as $key => [$href, $perm]) {
        if (archicad_bo_can($perm)) {
            $tab = $key;
            break;
        }
    }
}
header('Location: ' . ($map[$tab][0] ?? 'utilisateurs.php'));
exit;
