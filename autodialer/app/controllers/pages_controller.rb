class PagesController < ApplicationController
  def home
    @title = "Home Dashboard"
  end

  def make_call
    # 1. Get the raw text
    raw_input = params[:phone_numbers]

    if raw_input.present?
      # 2. Process the numbers
      numbers_list = raw_input.split(",").map(&:strip).reject(&:empty?)

      # 3. Loop and call service
      @results = numbers_list.map do |number|
        VonageService.make_call(number)
      end
      
      flash.now[:notice] = "Processed #{numbers_list.count} numbers."
      
      # SUCCESS: Render with 422 status so Turbo accepts the update
      @title = "Home Dashboard"
      render :home, status: :unprocessable_entity
    else
      flash.now[:alert] = "Please enter at least one number."
      
      # ERROR: Render with 422 status
      @title = "Home Dashboard"
      render :home, status: :unprocessable_entity
    end
  end
  # ... keep scrapper and blogs methods the same ...
  def scrapper
    @title = "Linkdine Scrapper"
  end

   def scrape_urls
    # 1. Get Input
    raw_input = params[:urls]

    if raw_input.present?
      urls_list = raw_input.split(",").map(&:strip).reject(&:empty?)

      @api_response = ScraperService.process(urls_list)
      flash.now[:notice] = "Scraping finished."
      
      # SUCCESS CASE: Render with status 422 or 200. 
      # In Rails 7, 422 ensures the page updates even without a redirect.
      render :scrapper, status: :unprocessable_entity
    else
      flash.now[:alert] = "Please enter at least one URL."
      
      # ERROR CASE: IMPORTANT! Add status: :unprocessable_entity
      render :scrapper, status: :unprocessable_entity
    end
  end

def blogs
    @title = "Blog Showcase"
    load_static_blogs
  end

  def generate_blog
      @title = "Blog Showcase"
      load_static_blogs # Vital to keep left sidebar visible

      title_input = params[:blog_title]
      details_input = params[:blog_details]

      if title_input.present?
        # Calling the correctly named class
        @generated_result = BlogService.generate(title_input, details_input)
        
        if @generated_result["error"]
          flash.now[:alert] = @generated_result["message"]
        else
          flash.now[:notice] = "Content generated successfully!"
        end

        # 422 is REQUIRED for the UI to update without a redirect in Turbo
        render :blogs, status: :unprocessable_entity 
      else
        flash.now[:alert] = "Title is required!"
        render :blogs, status: :unprocessable_entity
      end
    end

  private

  def load_static_blogs
    @static_blogs = [
      {
        title: "Understanding Rails MVC",
        data: "Model-View-Controller (MVC) is an architectural pattern that separates an application into three main logical components: the model, the view, and the controller..."
      },
      {
        title: "Why Linux is Better for Devs",
        data: "Linux offers superior package management, native support for most server-side languages, and a powerful terminal environment that Windows is still catching up to..."
      }
    ]
  end
end