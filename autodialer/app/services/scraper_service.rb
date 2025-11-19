require 'net/http'
require 'json'
require 'uri'

class ScraperService
  # Update this to where your FastAPI is running (usually port 8000)
  API_ENDPOINT = ENV['SCRAPER_API_URL'] || "http://192.168.0.171:8000/scrape"


  def self.process(urls_list)
    uri = URI(API_ENDPOINT)
    
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = (uri.scheme == 'https')
    
    # IMPORTANT: Increase timeout!
    # Since Python sleeps 5-10s per URL, we give it 5 minutes (300s) to finish.
    http.read_timeout = 300 
    
    request = Net::HTTP::Post.new(uri.path, {'Content-Type' => 'application/json'})
    
    # This matches your Python Pydantic model: class ScrapeRequest(BaseModel): urls: List[str]
    request.body = { urls: urls_list }.to_json

    begin
      response = http.request(request)

      if response.code.to_i >= 200 && response.code.to_i < 300
        return JSON.parse(response.body)
      else
        return { 
          "error" => "API Request Failed", 
          "code" => response.code, 
          "message" => response.message, 
          "body" => response.body 
        }
      end
    rescue Net::ReadTimeout
      return { "error" => "Timeout", "message" => "The scraper took too long to respond." }
    rescue => e
      return { "error" => "Connection Error", "message" => e.message }
    end
  end
end