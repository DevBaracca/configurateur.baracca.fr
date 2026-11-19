<?php
/**
 * Baracca - Back-office (configurateur.baracca.fr)
 * Téléchargement du JSON d'une soumission (réservé à l'administrateur)
 */

require_once __DIR__ . '/../includes/admin-auth.php';
require_once __DIR__ . '/../includes/soumissions.php';
require_once __DIR__ . '/../includes/acces.php';

archicad_bo_require('soumission');

$path = archicad_soumission_path((string) ($_GET['fichier'] ?? ''));
if ($path === null) {
    http_response_code(404);
    exit('Soumission introuvable.');
}

$fichier = basename($path);
// Filtrage par zone géographique : un vendeur/partenaire ne télécharge que
// les soumissions des clients de sa zone
$visibles = array_column(archicad_bo_filter_soumissions(archicad_load_soumissions()), 'fichier');
if (!in_array($fichier, $visibles, true)) {
    http_response_code(403);
    exit('Accès restreint à cette zone géographique.');
}
header('Content-Type: application/json; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $fichier . '"');
header('Content-Length: ' . (string) filesize($path));
readfile($path);
