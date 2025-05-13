<?php
// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// First part: MySQLi connection and table creation
define('DB_HOST', 'localhost');
define('DB_NAME', 'heritage_db');
define('DB_USER', 'root');
define('DB_PASS', '');

$conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$sql = "
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    city VARCHAR(50),
    category ENUM('endroit', 'objet', 'hotel', 'guide', 'transport'),
    image_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transport (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('taxi', 'avion', 'bus') NOT NULL,
    driver_name VARCHAR(100),
    contact VARCHAR(20),
    price DECIMAL(10,2),
    route VARCHAR(255),
    image_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT,
    user_id INT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
";

if ($conn->multi_query($sql)) {
    echo "Tables created successfully.<br>";
    while ($conn->next_result()) {;}
} else {
    die("Error creating tables: " . $conn->error);
}

$conn->close();

// Second part: PDO connection (used later in other files)
try {
    $db = new PDO("mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8", DB_USER, DB_PASS);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "PDO connection successful.";
} catch (PDOException $e) {
    die("PDO connection failed: " . $e->getMessage());
}
?>
