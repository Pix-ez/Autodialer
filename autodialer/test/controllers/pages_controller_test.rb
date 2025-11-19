require "test_helper"

class PagesControllerTest < ActionDispatch::IntegrationTest
  test "should get home" do
    get pages_home_url
    assert_response :success
  end

  test "should get scrapper" do
    get pages_scrapper_url
    assert_response :success
  end

  test "should get blogs" do
    get pages_blogs_url
    assert_response :success
  end
end
