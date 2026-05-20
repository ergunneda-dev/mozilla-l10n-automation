# Sample en-US Fluent file for smoke-testing the scripts.
# Mimics the shape of a real firefox-l10n entry: simple messages,
# attributes, variables, term references, and a selector.

-brand-short-name = Firefox

new-tab-button =
    .label = New tab
    .tooltiptext = Open a new tab

bookmarks-count =
    { $count ->
        [one] You have one bookmark
       *[other] You have { $count } bookmarks
    }

welcome-banner = Welcome to { -brand-short-name }, { $name }!

settings-saved = Your changes have been saved.
