<?php
require_once '../../config.php';
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];

switch ($method) {
    case 'GET':
        $type = isset($_GET['type']) ? $_GET['type'] : null;
        
        $sql = "SELECT * FROM transport";
        if ($type) {
            $sql .= " WHERE type = ?";
            $stmt = $conn->prepare($sql);
            $stmt->bind_param("s", $type);
        } else {
            $stmt = $conn->prepare($sql);
        }
        
        $stmt->execute();
        $result = $stmt->get_result();
        $transports = $result->fetch_all(MYSQLI_ASSOC);
        
        echo json_encode($transports);
        break;

    case 'POST':
        $data = json_decode(file_get_contents('php://input'), true);
        
        $stmt = $conn->prepare("INSERT INTO transport (type, driver_name, contact, price, route) VALUES (?, ?, ?, ?, ?)");
        $stmt->bind_param("sssss", $data['type'], $data['driver_name'], $data['contact'], $data['price'], $data['route']);
        
        if ($stmt->execute()) {
            echo json_encode(['success' => true]);
        } else {
            echo json_encode(['error' => 'Failed to add transport']);
        }
        break;

    default:
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
}
?>