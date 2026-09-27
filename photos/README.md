# Photos

Drop photos here using these exact file names (any of .jpg / .jpeg / .png / .webp / .heic),
then run `python3 build.py`. Images are resized and converted to WebP automatically.

| File name                 | Where it appears                                   |
|---------------------------|----------------------------------------------------|
| service-garage            | Garage Cleanouts card + page                       |
| service-junk              | Junk & Furniture Removal card + page               |
| service-hot-tub           | Hot Tub Removal card + page, home photo strip      |
| cleanout-in-progress      | Move-Out & Property Cleanouts card + page          |
| loaded-trailer            | Basement & Attic card + page (replace with a real basement/attic job when you have one) |
| crew-member               | Home "Local crew" section, About page, video poster |
| crew-vests                | Home "Local crew", About hero, photo strip         |
| disposal-dumpster         | Home "Donation & disposal", About page             |
| garage-after-wide         | Home photo strip                                   |

## Before / after sliders
Put pairs in `before-after/` named `<job>-before.jpg` and `<job>-after.jpg`
(e.g. `basement-derby-before.jpg` + `basement-derby-after.jpg`). Every pair shows up
automatically on the home page and every service-area page. Shoot both photos from
the same spot and angle — that's what makes the slider look great. Add a caption for
new pairs in `BA_CAPTIONS` inside `build.py`.

## Video
`video/garage-timelapse.mp4` plays in the home hero. `video/crew-intro.mp4` is on the About page.
Originals are kept in `_originals/` (not published).
