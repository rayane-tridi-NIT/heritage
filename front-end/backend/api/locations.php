<?php
require_once '../../config.php';
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];

switch ($method) {
    case 'GET':
        $category = isset($_GET['category']) ? $_GET['category'] : null;
        
        $sql = "SELECT * FROM locations";
        if ($category) {
            $sql .= " WHERE category = ?";
            $stmt = $conn->prepare($sql);
            $stmt->bind_param("s", $category);
        } else {
            $stmt = $conn->prepare($sql);
        }
        
        $stmt->execute();
        $result = $stmt->get_result();
        $locations = $result->fetch_all(MYSQLI_ASSOC);
        
        echo json_encode($locations);
        break;

    case 'POST':
        $data = json_decode(file_get_contents('php://input'), true);
        
        // Handle image upload
        $imagePath = null;
        if (isset($_FILES['image'])) {
            $targetDir = "../../uploads/";
            $imagePath = $targetDir . basename($_FILES['image']['name']);
            move_uploaded_file($_FILES['image']['tmp_name'], $imagePath);
        }
        
        $stmt = $conn->prepare("INSERT INTO locations (title, description, city, category, image_path) VALUES (?, ?, ?, ?, ?)");
        $stmt->bind_param("sssss", $data['title'], $data['description'], $data['city'], $data['category'], $imagePath);
        
        if ($stmt->execute()) {
            echo json_encode(['success' => true]);
        } else {
            echo json_encode(['error' => 'Failed to add location']);
        }
        break;

    default:
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
}
?>