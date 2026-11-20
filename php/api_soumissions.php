<?php
/**
 * Baracca - Site configurateur.baracca.fr
 * API back-office (même origine) : soumissions des clients.
 * Action (corps JSON en POST) : delete { fichier, csrf } — supprime le fichier
 * JSON de la soumission sans rechargement de page (consommée par
 * admin/soumissions.php, comme php/api_configurations.php pour « Mon compte »).
 * Réservé à une session back-office ayant accès à la rubrique « soumissions » ;
 * un vendeur/partenaire ne peut supprimer que les soumissions visibles dans sa
 * zone (même filtre que la liste de la page).
 */
require_once __DIR__ . '/../includes/acces.php';
require_once __DIR__ . '/../includes/soumissions.php';

// Réponses toujours en JSON pur (un warning PHP ne doit pas corrompre le payload)
ini_set('display_errors', '0');

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

if (!archicad_bo_is_logged_in() || !archicad_bo_can('soumissions')) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Accès restreint à la rubrique Soumissions.']);
    exit;
}

$body = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($body)) {
    $body = [];
}

if (!archicad_admin_csrf_verify($body['csrf'] ?? null)) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Jeton de sécurité invalide.']);
    exit;
}

$action = (string) ($body['action'] ?? '');

switch ($action) {
    case 'delete':
        $fichier = basename((string) ($body['fichier'] ?? ''));
        // Visibilité : mêmes règles que la liste affichée (zone du staff)
        $visible = false;
        foreach (archicad_bo_filter_soumissions(archicad_load_soumissions()) as $s) {
            if ((string) ($s['fichier'] ?? '') === $fichier) {
                $visible = true;
                break;
            }
        }
        if ($fichier === '' || !$visible) {
            http_response_code(404);
            echo json_encode(['ok' => false, 'error' => 'Soumission introuvable.']);
            break;
        }
        if (!archicad_delete_soumission($fichier)) {
            http_response_code(404);
            echo json_encode(['ok' => false, 'error' => 'Soumission introuvable.']);
            break;
        }
        echo json_encode(['ok' => true, 'fichier' => $fichier, 'restant' => archicad_soumissions_count()]);
        break;

    default:
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => 'Action inconnue.']);
}
