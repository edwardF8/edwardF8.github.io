# Rewrites root-relative URLs (e.g. src="/assets/img/foo.jpg") in the generated
# Atom/RSS feed to absolute URLs (e.g. https://<site.url>/assets/img/foo.jpg).
#
# Why: external importers/readers — notably Substack's RSS importer — do NOT
# resolve root-relative image/link paths against the site origin, so post images
# (and internal links) silently drop on import. Absolutizing them in the feed
# makes every image fetchable by any external reader, for all current and future
# posts, no matter how the image was written (Markdown ![](...), raw <img>,
# relative_url filter, or al-folio figure includes).
#
# Runs once after the whole site is written, editing _site/feed.xml in place.
# Touches ONLY the feed output — the website's own pages are untouched.
# No-op if `url:` is unset in _config.yml or feed.xml is absent.

Jekyll::Hooks.register :site, :post_write do |site|
  site_url = site.config["url"].to_s.chomp("/")
  next if site_url.empty?

  feed_path = File.join(site.dest, "feed.xml")
  next unless File.exist?(feed_path)

  content = File.read(feed_path)
  # Match src="/..." and href="/..." but skip protocol-relative "//..." URLs.
  updated = content.gsub(%r{\b(src|href)="/(?!/)}, %(\\1="#{site_url}/))

  if updated != content
    File.write(feed_path, updated)
    Jekyll.logger.info "Feed URLs:", "absolutized root-relative src/href in feed.xml"
  end
end
