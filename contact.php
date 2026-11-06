<?php
// Optic5 contact form handler (works on standard cPanel PHP hosting).
// Set the address that should receive inquiries:
$TO_EMAIL   = 'hello@optic5.com';
// Must be a mailbox on your own domain, or many hosts/receivers will reject it:
$FROM_EMAIL = 'no-reply@optic5.com';

$wantsJson = isset($_SERVER['HTTP_ACCEPT']) && strpos($_SERVER['HTTP_ACCEPT'], 'application/json') !== false;

function respond($ok, $error = '') {
    global $wantsJson;
    if ($wantsJson) {
        header('Content-Type: application/json');
        echo json_encode(['ok' => $ok, 'error' => $error]);
    } else {
        header('Location: /' . ($ok ? '?sent=1#contact' : '?sent=0#contact'));
    }
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    respond(false, 'Method not allowed');
}

// Honeypot: bots fill hidden fields
if (!empty($_POST['website'])) {
    respond(true);
}

function clean($key, $max = 200) {
    $v = isset($_POST[$key]) ? trim((string)$_POST[$key]) : '';
    $v = str_replace(["\r", "\n", "%0a", "%0d"], ' ', $v); // block header injection
    return mb_substr($v, 0, $max);
}

$name     = clean('name', 100);
$business = clean('business', 150);
$email    = clean('email', 150);
$phone    = clean('phone', 40);
$interest = clean('interest', 100);
$message  = isset($_POST['message']) ? mb_substr(trim((string)$_POST['message']), 0, 5000) : '';

if ($name === '' || $message === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    respond(false, 'Missing or invalid fields');
}

$subject = 'New Optic5 inquiry: ' . $name . ($business ? " ($business)" : '');
$body  = "Name: $name\n";
$body .= "Business: $business\n";
$body .= "Email: $email\n";
$body .= "Phone: $phone\n";
$body .= "Interest: $interest\n\n";
$body .= "Message:\n$message\n\n";
$body .= "--\nSent from optic5.com on " . date('Y-m-d H:i') . ' from IP ' . ($_SERVER['REMOTE_ADDR'] ?? '');

$headers  = "From: Optic5 Website <$FROM_EMAIL>\r\n";
$headers .= "Reply-To: $name <$email>\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

$sent = @mail($TO_EMAIL, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, $headers, '-f' . $FROM_EMAIL);
respond((bool)$sent, $sent ? '' : 'Mail server error');
