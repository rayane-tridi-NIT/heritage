<?php
function sanitizeInput($data) {
    global $conn;
    return $conn->real_escape_string(htmlspecialchars(trim($data)));
}

function isLoggedIn() {
    return isset($_SESSION['user_id']);
}

function getCurrentUser() {
    global $conn;
    if (isLoggedIn()) {
        $stmt = $conn->prepare("SELECT * FROM users WHERE id = ?");
        $stmt->bind_param("i", $_SESSION['user_id']);
        $stmt->execute();
        return $stmt->get_result()->fetch_assoc();
    }
    return null;
}
?>