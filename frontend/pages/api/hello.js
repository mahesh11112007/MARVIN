// Next.js API route example
// This API route returns JSON with proper headers

export default function handler(req, res) {
  // Set proper content-type header for JSON
  res.setHeader('Content-Type', 'application/json');
  
  // Return JSON response with status 200
  res.status(200).json({ 
    message: 'Hello from API',
    timestamp: new Date().toISOString(),
    method: req.method,
    status: 'success'
  });
}
