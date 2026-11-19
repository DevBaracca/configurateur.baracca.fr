<?php
/**
 * Baracca - Site configurateur.baracca.fr
 * Gestion des accès au back-office par rôle :
 *   - administrateur (data/admins.json) : accès à tout ;
 *   - vendeur / partenaire (data/users.json, role + acces[]) : accès au
 *     configurateur côté client (comme un client) + aux seules rubriques
 *     du back-office cochées dans leur fiche ;
 *   - client (data/users.json, role = client) : configurateur côté client seul.
 *
 * L'arborescence ci-dessous décrit les rubriques protégées du back-office ;
 * cocher un nœud parent autorise tous ses descendants.
 */

require_once __DIR__ . '/admin-auth.php';
require_once __DIR__ . '/users.php';

// ---------------------------------------------------------------------------
// Arborescence des rubriques du back-office (clés utilisées par archicad_bo_can)
// ---------------------------------------------------------------------------

function archicad_acces_tree(): array
{
    $sectionsConfig = [
        'modules' => 'Modules', 'isolation' => 'Isolation', 'formes' => 'Formes',
        'charpentes' => 'Charpentes', 'menuiseries' => 'Ouvrants', 'fenetres_toit' => 'Fenêtres de toit',
        'murs' => 'Murs', 'planchers' => 'Planchers', 'toitures' => 'Complexes de toiture',
        'surfaces' => 'Revêtements extérieurs', 'interieurs' => 'Revêtements intérieurs',
        'couvertures' => 'Couvertures de toiture', 'rev_plancher' => 'Revêtements de plancher',
        'systemes_aut' => 'Systèmes d\'autonomie', 'equipements' => 'Équipements',
        'autonomie' => 'Packs autonomie', 'amenagements' => 'Packs aménagements',
        'promotions' => 'Promotions', 'modeles' => 'Modèles',
    ];
    $children = [];
    foreach ($sectionsConfig as $key => $label) {
        $children[] = ['key' => 'configurateur:' . $key, 'label' => $label, 'children' => []];
    }
    return [
        ['key' => 'index', 'label' => 'Tableau de bord', 'children' => []],
        ['key' => 'soumissions', 'label' => 'Soumissions', 'children' => [
            ['key' => 'soumission', 'label' => 'Téléchargement du JSON des soumissions', 'children' => []],
        ]],
        ['key' => 'configurateur', 'label' => 'Configurateur (tous les catalogues)', 'children' => $children],
        ['key' => 'comptes', 'label' => 'Gestion des comptes', 'children' => [
            ['key' => 'utilisateurs', 'label' => 'Utilisateurs (clients)', 'children' => []],
            ['key' => 'vendeurs', 'label' => 'Vendeurs', 'children' => []],
            ['key' => 'partenaires', 'label' => 'Partenaires', 'children' => []],
            ['key' => 'administrateurs', 'label' => 'Administrateurs', 'children' => []],
        ]],
    ];
}

// Toutes les clés de l'arborescence (à plat)
function archicad_acces_all_keys(): array
{
    $keys = [];
    $walk = function (array $nodes) use (&$walk, &$keys) {
        foreach ($nodes as $n) {
            $keys[] = $n['key'];
            $walk($n['children']);
        }
    };
    $walk(archicad_acces_tree());
    return $keys;
}

// Clés d'un nœud et de tous ses descendants
function archicad_acces_key_and_descendants(string $key): array
{
    $out = [$key];
    $walk = function (array $nodes) use (&$walk, &$out, $key) {
        foreach ($nodes as $n) {
            if ($n['key'] === $key) {
                foreach ($n['children'] as $c) {
                    $out = array_merge($out, archicad_acces_key_and_descendants($c['key']));
                }
                return;
            }
            $walk($n['children']);
        }
    };
    $walk(archicad_acces_tree());
    return array_values(array_unique($out));
}

// ---------------------------------------------------------------------------
// Session back-office : rôle effectif ('admin' | 'vendeur' | 'partenaire' | null)
// ---------------------------------------------------------------------------

function archicad_bo_role(): ?string
{
    if (archicad_admin_is_logged_in()) {
        return 'admin';
    }
    $id = (string) ($_SESSION['archicad_user_id'] ?? '');
    if ($id === '') {
        return null;
    }
    $user = archicad_find_user_by_id($id);
    if ($user === null) {
        return null;
    }
    $role = archicad_user_role($user);
    return in_array($role, archicad_bo_roles(), true) ? $role : null;
}

// Connecté au back-office : administrateur OU compte vendeur/partenaire
function archicad_bo_is_logged_in(): bool
{
    return archicad_bo_role() !== null;
}

// Compte staff actuellement connecté (vendeur/partenaire), ou null
function archicad_bo_current_staff(): ?array
{
    $id = (string) ($_SESSION['archicad_user_id'] ?? '');
    if ($id === '' || archicad_admin_is_logged_in()) {
        return null;
    }
    $user = archicad_find_user_by_id($id);
    if ($user === null || !in_array(archicad_user_role($user), archicad_bo_roles(), true)) {
        return null;
    }
    return $user;
}

/**
 * Connexion au back-office : identifiant + mot de passe d'un administrateur,
 * OU email + mot de passe d'un compte vendeur/partenaire (la session client
 * est alors posée : le configurateur en ligne reste accessible).
 */
function archicad_bo_login(string $identifier, string $password): bool
{
    if (archicad_admin_login($identifier, $password)) {
        return true;
    }
    $user = archicad_find_user_by_email($identifier);
    if ($user !== null && password_verify($password, (string) $user['hash'])
        && in_array(archicad_user_role($user), archicad_bo_roles(), true)) {
        session_regenerate_id(true);
        // Une seule identité par session : on écarte une éventuelle session admin
        unset($_SESSION['archicad_admin'], $_SESSION['archicad_admin_username']);
        $_SESSION['archicad_user_id'] = (string) $user['id'];
        archicad_touch_login((string) $user['id']);
        if (function_exists('archicad_stats_log_login')) {
            archicad_stats_log_login((string) $user['id']);
        }
        return true;
    }
    return false;
}

// ---------------------------------------------------------------------------
// Droits : un administrateur a accès à tout ; un vendeur/partenaire aux seules
// rubriques cochées (un nœud coché couvre tous ses descendants).
// ---------------------------------------------------------------------------

function archicad_bo_can(string $key): bool
{
    $role = archicad_bo_role();
    if ($role === 'admin') {
        return true;
    }
    $staff = archicad_bo_current_staff();
    if ($staff === null) {
        return false;
    }
    $acces = array_map('strval', (array) ($staff['acces'] ?? []));
    foreach ($acces as $a) {
        if (in_array($key, archicad_acces_key_and_descendants($a), true)) {
            return true;
        }
    }
    return false;
}

// Garde-fou d'une page/section du back-office : redirige vers la connexion si
// personne n'est connecté, affiche « Accès restreint » si le rôle ne convient pas.
function archicad_bo_require(string $key): void
{
    if (!archicad_bo_is_logged_in()) {
        header('Location: index.php');
        exit;
    }
    if (archicad_bo_can($key)) {
        return;
    }
    $role = archicad_bo_role();
    $pageTitle = 'Accès restreint';
    $adminPage = '';
    include __DIR__ . '/admin-head.php';
    $staff = archicad_bo_current_staff();
    echo '<div class="admin-card"><h1>Accès restreint</h1>';
    echo '<p class="admin-hint">Votre compte' . ($staff !== null ? ' « ' . htmlspecialchars(trim((string) ($staff['prenom'] ?? '') . ' ' . (string) ($staff['nom'] ?? ''))) . ' » (' . htmlspecialchars(archicad_user_role($staff)) . ')' : '') . ' n\'a pas accès à cette rubrique du back-office.</p>';
    // Rubriques autorisées : premier niveau de l'arborescence cochée
    $autorisees = [];
    if ($staff !== null) {
        $acces = array_map('strval', (array) ($staff['acces'] ?? []));
        foreach (archicad_acces_tree() as $n) {
            if (in_array($n['key'], $acces, true)) {
                $autorisees[] = $n['label'];
            }
        }
    }
    if ($autorisees !== []) {
        echo '<p class="admin-hint">Rubriques ouvertes : <strong>' . htmlspecialchars(implode(', ', $autorisees)) . '</strong>.</p>';
    }
    // Lien de retour vers la première rubrique autorisée
    $homeHref = 'index.php';
    $homeLabel = 'Retour au tableau de bord';
    foreach (archicad_acces_tree() as $n) {
        if (!archicad_bo_can((string) $n['key'])) {
            continue;
        }
        if ($n['key'] === 'soumissions') { $homeHref = 'soumissions.php'; $homeLabel = 'Retour aux soumissions'; }
        elseif ($n['key'] === 'configurateur') { $homeHref = archicad_bo_configurateur_home() ?? 'configurateur.php'; $homeLabel = 'Retour au configurateur'; }
        elseif ($n['key'] === 'comptes') { $homeHref = 'comptes.php'; $homeLabel = 'Retour à la gestion des comptes'; }
        break;
    }
    echo '<p><a href="' . htmlspecialchars($homeHref) . '" class="btn btn-secondary">' . htmlspecialchars($homeLabel) . '</a></p></div>';
    include __DIR__ . '/admin-footer.php';
    exit;
}

// Première section du configurateur autorisée (pour le lien du menu)
function archicad_bo_configurateur_home(): ?string
{
    if (archicad_bo_can('configurateur')) {
        return 'configurateur.php';
    }
    foreach (archicad_acces_tree() as $n) {
        if ($n['key'] !== 'configurateur') {
            continue;
        }
        foreach ($n['children'] as $c) {
            if (archicad_bo_can($c['key'])) {
                return 'configurateur.php?section=' . urlencode(str_replace('configurateur:', '', $c['key']));
            }
        }
    }
    return null;
}

// ---------------------------------------------------------------------------
// Vues : arborescence à cocher (fiche vendeur/partenaire) et onglets « Gestion des comptes »
// ---------------------------------------------------------------------------

// Rend l'arborescence des accès avec cases à cocher (name="acces[]")
function archicad_acces_checkbox(array $node, array $acces, int $depth = 0): void
{
    $key = (string) $node['key'];
    $checked = in_array($key, $acces, true) ? ' checked' : '';
    echo '<label class="acces-item" style="margin-left:' . ($depth * 20) . 'px">'
        . '<input type="checkbox" name="acces[]" value="' . htmlspecialchars($key) . '"' . $checked . '> '
        . htmlspecialchars((string) $node['label']) . '</label>';
    foreach ($node['children'] as $c) {
        archicad_acces_checkbox($c, $acces, $depth + 1);
    }
}

// Barre d'onglets de la rubrique « Gestion des comptes » (onglets filtrés selon les droits)
function archicad_comptes_tabs(string $actif): void
{
    $tabs = [
        ['utilisateurs', 'Utilisateurs', 'utilisateurs.php', 'utilisateurs'],
        ['vendeurs', 'Vendeurs', 'staff.php?role=vendeur', 'vendeurs'],
        ['partenaires', 'Partenaires', 'staff.php?role=partenaire', 'partenaires'],
        ['administrateurs', 'Administrateurs', 'administrateurs.php', 'administrateurs'],
    ];
    echo '<nav class="admin-tabs admin-subtabs">';
    foreach ($tabs as [$key, $label, $href, $perm]) {
        if (!archicad_bo_can($perm)) {
            continue;
        }
        echo '<a href="' . $href . '"' . ($actif === $key ? ' class="active"' : '') . '>' . $label . '</a>';
    }
    echo '</nav>';
}

// ---------------------------------------------------------------------------
// Zones géographiques : départements attribués à un vendeur/partenaire.
// Le département d'un client est déduit de son code postal.
// ---------------------------------------------------------------------------

// Carte des départements : code => [x, y, nom] (cartogramme en tuiles 15×14,
// métropole + Corse + DOM-TOM en rangée du bas)
function archicad_departements(): array
{
    return [
        '59' => [6, 0, 'Nord'],
        '62' => [5, 1, 'Pas-de-Calais'], '80' => [7, 1, 'Somme'], '08' => [9, 1, 'Ardennes'],
        '76' => [6, 2, 'Seine-Maritime'], '60' => [7, 2, 'Oise'], '02' => [8, 2, 'Aisne'], '51' => [9, 2, 'Marne'], '57' => [11, 2, 'Moselle'],
        '29' => [1, 3, 'Finistère'], '22' => [2, 3, 'Côtes-d\'Armor'], '50' => [3, 3, 'Manche'], '14' => [4, 3, 'Calvados'], '27' => [5, 3, 'Eure'], '95' => [7, 3, 'Val-d\'Oise'], '93' => [8, 3, 'Seine-Saint-Denis'], '10' => [9, 3, 'Aube'], '55' => [10, 3, 'Meuse'], '54' => [11, 3, 'Meurthe-et-Moselle'], '88' => [12, 3, 'Vosges'], '67' => [13, 3, 'Bas-Rhin'],
        '35' => [2, 4, 'Ille-et-Vilaine'], '53' => [3, 4, 'Mayenne'], '61' => [4, 4, 'Orne'], '28' => [6, 4, 'Eure-et-Loir'], '78' => [7, 4, 'Yvelines'], '75' => [8, 4, 'Paris'], '94' => [9, 4, 'Val-de-Marne'], '52' => [10, 4, 'Haute-Marne'], '68' => [13, 4, 'Haut-Rhin'],
        '44' => [1, 5, 'Loire-Atlantique'], '49' => [2, 5, 'Maine-et-Loire'], '72' => [4, 5, 'Sarthe'], '92' => [7, 5, 'Hauts-de-Seine'], '91' => [8, 5, 'Essonne'], '21' => [10, 5, 'Côte-d\'Or'], '77' => [9, 5, 'Seine-et-Marne'], '70' => [12, 5, 'Haute-Saône'],
        '56' => [1, 6, 'Morbihan'], '85' => [2, 6, 'Vendée'], '79' => [3, 6, 'Deux-Sèvres'], '86' => [4, 6, 'Vienne'], '37' => [5, 6, 'Indre-et-Loire'], '41' => [6, 6, 'Loir-et-Cher'], '18' => [7, 6, 'Cher'], '45' => [8, 6, 'Loiret'], '89' => [10, 6, 'Yonne'], '25' => [11, 6, 'Doubs'], '90' => [13, 6, 'Territoire de Belfort'],
        '17' => [2, 7, 'Charente-Maritime'], '36' => [5, 7, 'Indre'], '23' => [6, 7, 'Creuse'], '58' => [7, 7, 'Nièvre'], '03' => [8, 7, 'Allier'], '71' => [10, 7, 'Saône-et-Loire'], '39' => [11, 7, 'Jura'],
        '16' => [3, 8, 'Charente'], '24' => [4, 8, 'Dordogne'], '87' => [5, 8, 'Haute-Vienne'], '19' => [6, 8, 'Corrèze'], '63' => [7, 8, 'Puy-de-Dôme'], '69' => [9, 8, 'Rhône'], '01' => [10, 8, 'Ain'], '73' => [11, 8, 'Savoie'], '74' => [12, 8, 'Haute-Savoie'], '2B' => [14, 8, 'Haute-Corse'],
        '33' => [1, 9, 'Gironde'], '47' => [4, 9, 'Lot-et-Garonne'], '46' => [5, 9, 'Lot'], '12' => [6, 9, 'Aveyron'], '15' => [7, 9, 'Cantal'], '43' => [8, 9, 'Haute-Loire'], '42' => [9, 9, 'Loire'], '26' => [10, 9, 'Drôme'], '38' => [11, 9, 'Isère'], '05' => [12, 9, 'Hautes-Alpes'],
        '40' => [2, 10, 'Landes'], '32' => [4, 10, 'Gers'], '82' => [5, 10, 'Tarn-et-Garonne'], '31' => [6, 10, 'Haute-Garonne'], '81' => [7, 10, 'Tarn'], '48' => [8, 10, 'Lozère'], '84' => [9, 10, 'Vaucluse'], '07' => [10, 10, 'Ardèche'], '13' => [11, 10, 'Bouches-du-Rhône'], '04' => [12, 10, 'Alpes-de-Haute-Provence'], '06' => [13, 10, 'Alpes-Maritimes'], '2A' => [14, 10, 'Corse-du-Sud'],
        '64' => [2, 11, 'Pyrénées-Atlantiques'], '65' => [3, 11, 'Hautes-Pyrénées'], '09' => [5, 11, 'Ariège'], '11' => [6, 11, 'Aude'], '34' => [8, 11, 'Hérault'], '30' => [9, 11, 'Gard'], '83' => [12, 11, 'Var'],
        '66' => [7, 12, 'Pyrénées-Orientales'],
        // DOM-TOM (rangée du bas)
        '971' => [0, 13, 'Guadeloupe'], '972' => [1, 13, 'Martinique'], '973' => [2, 13, 'Guyane'], '974' => [3, 13, 'La Réunion'], '975' => [4, 13, 'Saint-Pierre-et-Miquelon'], '976' => [5, 13, 'Mayotte'], '977' => [6, 13, 'Saint-Barthélemy'], '978' => [7, 13, 'Saint-Martin'],
    ];
}

// Département déduit du code postal : 2 premiers chiffres (métropole),
// 2A/2B pour la Corse (20xxx), 3 premiers chiffres pour les DOM-TOM (97xxx+)
function archicad_user_departement(string $codePostal): string
{
    $cp = preg_replace('/\D/', '', $codePostal);
    if (strlen($cp) < 2) {
        return '';
    }
    if (substr($cp, 0, 2) === '20') {
        return ((int) $cp < 20200) ? '2A' : '2B';
    }
    if ((int) substr($cp, 0, 2) >= 97 && strlen($cp) >= 3) {
        return substr($cp, 0, 3);
    }
    return str_pad(substr($cp, 0, 2), 2, '0', STR_PAD_LEFT);
}

// Un staff ne voit que les clients de sa zone géographique (départements
// attribués). Admin = tout ; staff sans zone définie = tout ; client sans
// code postal = visible (zone inconnue).
function archicad_bo_user_visible(array $user): bool
{
    $staff = archicad_bo_current_staff();
    if ($staff === null) {
        return true; // administrateur : voit tout
    }
    $deps = array_map('strval', (array) ($staff['departements'] ?? []));
    if ($deps === []) {
        return true; // aucune zone attribuée : pas de restriction
    }
    $dept = archicad_user_departement((string) ($user['code_postal'] ?? ''));
    if ($dept === '') {
        return true; // client sans code postal : visible
    }
    return in_array($dept, $deps, true);
}

// Filtre une liste de comptes clients selon la zone du staff connecté
function archicad_bo_filter_users(array $users): array
{
    return array_values(array_filter($users, 'archicad_bo_user_visible'));
}

// Filtre les soumissions : un staff ne voit que celles des clients de sa zone
function archicad_bo_filter_soumissions(array $soumissions): array
{
    $staff = archicad_bo_current_staff();
    if ($staff === null) {
        return $soumissions; // administrateur : tout
    }
    return array_values(array_filter($soumissions, function ($s) {
        $auteur = $s['utilisateur']['email'] ?? '';
        if ($auteur === '') {
            return true;
        }
        $user = archicad_find_user_by_email((string) $auteur);
        if ($user === null) {
            return true; // auteur inconnu (ex. admin) : visible
        }
        return archicad_bo_user_visible($user);
    }));
}

// Carte interactive des départements (tuiles cliquables = cases à cocher)
function archicad_departements_carte(array $selectionnes): void
{
    $sel = array_map('strval', $selectionnes);
    $tile = 38; // px
    $cols = 15;
    $rows = 14;
    echo '<div class="dept-carte" style="width:' . ($cols * $tile) . 'px;height:' . ($rows * $tile) . 'px" role="group" aria-label="Carte des départements">';
    foreach (archicad_departements() as $code => [$x, $y, $nom]) {
        $checked = in_array((string) $code, $sel, true);
        echo '<label class="dept-tile" style="left:' . ($x * $tile) . 'px;top:' . ($y * $tile) . 'px" title="' . htmlspecialchars($nom . ' (' . $code . ')') . '">'
            . '<input type="checkbox" name="departements[]" value="' . htmlspecialchars((string) $code) . '"' . ($checked ? ' checked' : '') . '>'
            . '<span>' . htmlspecialchars((string) $code) . '</span></label>';
    }
    echo '</div>';
}
