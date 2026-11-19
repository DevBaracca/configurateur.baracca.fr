<?php
/**
 * Baracca - Back-office (configurateur.baracca.fr)
 * Rubrique « Gestion des comptes » : redirige vers l'onglet demandé
 * (utilisateurs / vendeurs / partenaires / administrateurs).
 */

require_once __DIR__ . '/../includes/admin-auth.php';
require_once __DIR__ . '/../includes/acces.php';

archicad_bo_require('comptes');

$tab = (string) ($_GET['tab'] ?? 'utilisateurs');
$map = [
    'utilisateurs' => 'utilisateurs.php',
    'vendeurs' => 'staff.php?role=vendeur',
    'partenaires' => 'staff.php?role=partenaire',
    'administrateurs' => 'administrateurs.php',
];
header('Location: ' . ($map[$tab] ?? 'utilisateurs.php'));
exit;
