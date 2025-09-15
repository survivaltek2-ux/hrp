import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import "https://deno.land/x/xhr@0.1.0/mod.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const username = Deno.env.get('RACING_API_USERNAME');
    const password = Deno.env.get('RACING_API_PASSWORD');
    
    if (!username || !password) {
      throw new Error('Racing API credentials not configured');
    }

    // Create basic auth header
    const credentials = btoa(`${username}:${password}`);
    const authHeader = `Basic ${credentials}`;

    const { endpoint } = await req.json();
    
    // Default to races endpoint if not specified
    const apiEndpoint = endpoint || '/races/today';
    
    console.log(`Fetching racing data from: ${apiEndpoint}`);

    // You'll need to replace this with the actual racing API base URL
    const baseUrl = 'https://api.racing-service.com'; // Replace with actual API URL
    
    const response = await fetch(`${baseUrl}${apiEndpoint}`, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      console.error(`API request failed: ${response.status} ${response.statusText}`);
      throw new Error(`Racing API returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Successfully fetched racing data');

    return new Response(JSON.stringify(data), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in fetch-racing-data function:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message,
        details: 'Check function logs for more information'
      }), 
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});