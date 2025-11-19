require 'net/http'
require 'json'
require 'uri'

class BlogService
  API_URL = "https://api.groq.com/openai/v1/chat/completions"
  
  # The specific system prompt from your CURL command
  SYSTEM_PROMPT = <<~HEREDOC
    You are an LLM specialized in producing clear, accurate, well-structured technical articles and blog posts. Your job is to take a user-provided title and supporting details, then generate a concise, technically correct, and reader-friendly article.

    REQUIRED BEHAVIOR:
    1. Use precise technical terminology where appropriate.
    2. Use analogies only when they improve clarity.
    3. Maintain a friendly, accessible tone without oversimplifying.
    4. Organize content logically (introduction, core explanation, examples, conclusion).
    5. Avoid unnecessary length; prioritize clarity and relevance.
    6. Produce well-structured paragraphs, clean formatting, and coherent flow.
    7. Do not invent details not implied by the title or user-provided information.
    8. Output **strict JSON** containing only the article fields.

    OUTPUT FORMAT (STRICT JSON):
    {
      "title": "<article title>",
      "content": "<full article>"
    }
  HEREDOC

  def self.generate(title, details)
    uri = URI(API_URL)
    
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true
    http.read_timeout = 60 # LLMs can take time

    request = Net::HTTP::Post.new(uri.path, {
      'Content-Type' => 'application/json',
      'Authorization' => "Bearer #{ENV['GROQ_API_KEY']}"
    })

    # Constructing the payload exactly as requested
    payload = {
      model: "openai/gpt-oss-20b",
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: "generate article on this title= #{title}, details= \"#{details}\"" }
      ],
      temperature: 0.59,
      max_completion_tokens: 8192,
      top_p: 1,
      stream: false,
      response_format: { type: "json_object" }
    }

    request.body = payload.to_json

    begin
      response = http.request(request)
      
      if response.code.to_i == 200
        json_response = JSON.parse(response.body)
        
        # Extract the content string from Groq response
        raw_content = json_response.dig("choices", 0, "message", "content")
        
        # The content itself is a JSON string, so we parse it again
        return JSON.parse(raw_content)
      else
        return { "error" => true, "message" => "API Error: #{response.code} - #{response.message}" }
      end
    rescue JSON::ParserError
      return { "error" => true, "message" => "Failed to parse LLM JSON response." }
    rescue => e
      return { "error" => true, "message" => e.message }
    end
  end
end