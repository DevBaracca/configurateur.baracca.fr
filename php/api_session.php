<?php
/**
 * Baracca - Site configurateur.baracca.fr
 * API (même origine) : état de la session client, consommée par l'application
 * React du configurateur (servie sous /configurateur/, intégrée par iframe).
 * N'expose jamais le hash du mot de passe.
 */
require_once __DIR__ . '/../includes/auth.php';

// Réponses toujours en JSON pur (un warning PHP ne doit pas corrompre le payload)
ini_set('display_errors', '0');

header('Content-Type: application/json; charset=utf-8');

// Compte client, ou session administrateur (id dédié « admin:<username> »)
$user = archicad_api_user();
if ($user === null) {
    echo json_encode(['loggedIn' => false, 'admin' => false, 'user' => null]);
} else {
    echo json_encode([
        'loggedIn' => true,
        'admin' => !empty($user['admin']),
        'user' => [
            'id' => (string) $user['id'],
            'email' => (string) ($user['email'] ?? ''),
            'nom' => (string) ($user['nom'] ?? ''),
            'prenom' => (string) ($user['prenom'] ?? ''),
        ],
    ]);
}
