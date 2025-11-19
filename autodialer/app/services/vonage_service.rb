require 'vonage'
require 'dotenv/load'


class VonageService
  def self.make_call(to_number)
    # Initialize the client
    client = Vonage::Client.new(
      application_id: ENV['VONAGE_APPLICATION_ID'],
      private_key: File.read(ENV['VONAGE_PRIVATE_KEY_PATH'])
    )

    # Make the call
    response = client.voice.create(
      to: [{
        type: 'phone',
        number: to_number
      }],
      from: {
        type: 'phone',
        number: ENV['VONAGE_VIRTUAL_NUMBER']
      },
      answer_url: [
        ENV['VOICE_ANSWER_URL']
      ]
    )
    
    # 3. Return Success Data
    return { 
      number: to_number, 
      status: "Called", 
      details: "UUID: #{response.uuid}" 
    }

  rescue => e
    # 4. Return Error Data if it crashes
    return { 
      number: to_number, 
      status: "Failed", 
      details: e.message 
    }
  end
end