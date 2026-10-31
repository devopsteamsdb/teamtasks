Add-Type -AssemblyName System.Drawing

function New-Canvas {
    param($c1, $c2)
    $bmp = New-Object System.Drawing.Bitmap 320, 320
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

    $p1 = [System.Drawing.Point]::new(0, 0)
    $p2 = [System.Drawing.Point]::new(320, 320)
    $brush = [System.Drawing.Drawing2D.LinearGradientBrush]::new($p1, $p2, $c1, $c2)
    $rect = New-Object System.Drawing.Rectangle 0, 0, 320, 320
    $g.FillRectangle($brush, $rect)
    $brush.Dispose()
    return @{ Bmp = $bmp; G = $g }
}

function Save-Avatar {
    param($canvas, $path)
    $canvas.G.Dispose()
    $canvas.Bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $canvas.Bmp.Dispose()
}

# -------------------------------------------------------------
# 31. Wolverine
# -------------------------------------------------------------
function Gen-31 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 245, 175, 25)) ([System.Drawing.Color]::FromArgb(255, 220, 110, 5))
    $g = $c.G

    # Shoulders (Blue & Yellow)
    $bSuit = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 20, 70, 165))
    $g.FillPolygon($bSuit, @(
        (New-Object System.Drawing.Point 40, 320),
        (New-Object System.Drawing.Point 75, 220),
        (New-Object System.Drawing.Point 245, 220),
        (New-Object System.Drawing.Point 280, 320)
    ))
    $bSuit.Dispose()

    # Chest yellow center
    $bYel = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 250, 195, 20))
    $g.FillPolygon($bYel, @(
        (New-Object System.Drawing.Point 110, 320),
        (New-Object System.Drawing.Point 125, 240),
        (New-Object System.Drawing.Point 195, 240),
        (New-Object System.Drawing.Point 210, 320)
    ))

    # Black tiger stripes on shoulders
    $bBlk = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 25, 30))
    $g.FillPolygon($bBlk, @( (New-Object System.Drawing.Point 75, 220), (New-Object System.Drawing.Point 115, 250), (New-Object System.Drawing.Point 105, 275), (New-Object System.Drawing.Point 65, 250) ))
    $g.FillPolygon($bBlk, @( (New-Object System.Drawing.Point 245, 220), (New-Object System.Drawing.Point 205, 250), (New-Object System.Drawing.Point 215, 275), (New-Object System.Drawing.Point 255, 250) ))

    # Neck
    $bSkin = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 250, 205, 165))
    $g.FillRectangle($bSkin, 138, 190, 44, 45)

    # Black Cowl Wings
    $g.FillPolygon($bBlk, @(
        (New-Object System.Drawing.Point 120, 140),
        (New-Object System.Drawing.Point 30, 40),
        (New-Object System.Drawing.Point 60, 95),
        (New-Object System.Drawing.Point 45, 125),
        (New-Object System.Drawing.Point 110, 180)
    ))
    $g.FillPolygon($bBlk, @(
        (New-Object System.Drawing.Point 200, 140),
        (New-Object System.Drawing.Point 290, 40),
        (New-Object System.Drawing.Point 260, 95),
        (New-Object System.Drawing.Point 275, 125),
        (New-Object System.Drawing.Point 210, 180)
    ))

    # Yellow Cowl
    $g.FillEllipse($bYel, 95, 65, 130, 145)

    # Exposed jaw / chin
    $g.FillPie($bSkin, 110, 125, 100, 90, 0, 180)

    # Stubble
    $pStubble = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(90, 60, 40, 30)), 3
    $g.DrawArc($pStubble, 122, 150, 76, 52, 10, 160)
    $pStubble.Dispose()

    # Confident mouth
    $pMouth = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 140, 50, 40)), 3
    $g.DrawArc($pMouth, 135, 172, 50, 22, 20, 140)
    $pMouth.Dispose()

    # White angled eye lenses (slanted up-and-outward, fierce Wolverine cowl eyes)
    $bWht = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 25, 25, 30)), 2
    $ptsL = @( (New-Object System.Drawing.Point 115, 125), (New-Object System.Drawing.Point 145, 138), (New-Object System.Drawing.Point 142, 146), (New-Object System.Drawing.Point 120, 140) )
    $ptsR = @( (New-Object System.Drawing.Point 205, 125), (New-Object System.Drawing.Point 175, 138), (New-Object System.Drawing.Point 178, 146), (New-Object System.Drawing.Point 200, 140) )
    $g.FillPolygon($bWht, $ptsL); $g.DrawPolygon($pEye, $ptsL)
    $g.FillPolygon($bWht, $ptsR); $g.DrawPolygon($pEye, $ptsR)

    $bYel.Dispose(); $bBlk.Dispose(); $bSkin.Dispose(); $bWht.Dispose(); $pEye.Dispose()
    Save-Avatar $c "static/avatars/avatar_31.png"
}

# -------------------------------------------------------------
# 32. Thor
# -------------------------------------------------------------
function Gen-32 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 45, 65, 95)) ([System.Drawing.Color]::FromArgb(255, 25, 35, 55))
    $g = $c.G

    # Red Cape
    $bCape = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 185, 25, 35))
    $g.FillPolygon($bCape, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 75, 215), (New-Object System.Drawing.Point 245, 215), (New-Object System.Drawing.Point 280, 320) ))
    $bCape.Dispose()

    # Armor Body
    $bArmor = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 50, 55, 65))
    $g.FillPolygon($bArmor, @( (New-Object System.Drawing.Point 80, 320), (New-Object System.Drawing.Point 95, 230), (New-Object System.Drawing.Point 225, 230), (New-Object System.Drawing.Point 240, 320) ))
    $bArmor.Dispose()

    # Silver Armor Discs
    $bDisc = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 205, 215, 225))
    $g.FillEllipse($bDisc, 115, 245, 32, 32)
    $g.FillEllipse($bDisc, 173, 245, 32, 32)
    $bDisc.Dispose()

    # Blond flowing hair background
    $bHair = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 205, 80))
    $g.FillEllipse($bHair, 85, 75, 150, 160)

    # Face & Neck
    $bSkin = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 250, 210, 170))
    $g.FillRectangle($bSkin, 138, 180, 44, 45)
    $g.FillEllipse($bSkin, 105, 85, 110, 115)

    # Silver Winged Helmet
    $bHelm = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 180, 190, 200))
    $g.FillPie($bHelm, 98, 65, 124, 110, 180, 180)
    $g.FillRectangle($bHelm, 153, 60, 14, 55) # nose guard strip

    # Helmet Wings (Left & Right)
    $bWing = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillPolygon($bWing, @( (New-Object System.Drawing.Point 105, 100), (New-Object System.Drawing.Point 40, 35), (New-Object System.Drawing.Point 65, 75), (New-Object System.Drawing.Point 50, 95), (New-Object System.Drawing.Point 102, 120) ))
    $g.FillPolygon($bWing, @( (New-Object System.Drawing.Point 215, 100), (New-Object System.Drawing.Point 280, 35), (New-Object System.Drawing.Point 255, 75), (New-Object System.Drawing.Point 270, 95), (New-Object System.Drawing.Point 218, 120) ))
    $bWing.Dispose(); $bHelm.Dispose()

    # Blond Beard
    $g.FillPie($bHair, 115, 135, 90, 65, 0, 180)

    # Eyes & Mouth
    $bEye = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 50, 140, 220))
    $g.FillEllipse($bEye, 126, 125, 12, 12)
    $g.FillEllipse($bEye, 182, 125, 12, 12)
    $pMouth = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 160, 90, 30)), 3
    $g.DrawLine($pMouth, 146, 165, 174, 165)

    $bHair.Dispose(); $bSkin.Dispose(); $bEye.Dispose(); $pMouth.Dispose()
    Save-Avatar $c "static/avatars/avatar_32.png"
}

# -------------------------------------------------------------
# 33. Black Panther
# -------------------------------------------------------------
function Gen-33 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 40, 20, 65)) ([System.Drawing.Color]::FromArgb(255, 15, 10, 30))
    $g = $c.G

    # Body
    $bSuit = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 25, 30))
    $g.FillPolygon($bSuit, @( (New-Object System.Drawing.Point 50, 320), (New-Object System.Drawing.Point 80, 215), (New-Object System.Drawing.Point 240, 215), (New-Object System.Drawing.Point 270, 320) ))

    # Vibranium purple accent lines
    $pPurl = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(180, 150, 50, 240)), 3
    $g.DrawLine($pPurl, 85, 230, 135, 300)
    $g.DrawLine($pPurl, 235, 230, 185, 300)
    $g.DrawLine($pPurl, 160, 235, 160, 310)

    # Panther Neck
    $g.FillRectangle($bSuit, 138, 185, 44, 45)

    # Silver Vibranium Claw Necklace
    $bSilv = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 215, 220, 230))
    for ($i = -4; $i -le 4; $i++) {
        $ang = $i * 12
        $cx = 160 + ($i * 12)
        $cy = 215 + ([Math]::Abs($i) * 2.5)
        $g.FillPolygon($bSilv, @(
            (New-Object System.Drawing.Point ($cx - 4), $cy),
            (New-Object System.Drawing.Point ($cx + 4), $cy),
            (New-Object System.Drawing.Point $cx, ($cy + 15))
        ))
    }

    # Head (Ears first)
    $g.FillPolygon($bSuit, @( (New-Object System.Drawing.Point 100, 100), (New-Object System.Drawing.Point 85, 45), (New-Object System.Drawing.Point 125, 75) ))
    $g.FillPolygon($bSuit, @( (New-Object System.Drawing.Point 220, 100), (New-Object System.Drawing.Point 235, 45), (New-Object System.Drawing.Point 195, 75) ))

    # Head oval
    $g.FillEllipse($bSuit, 95, 65, 130, 145)

    # Silver tribal brow and cheek markings
    $pSilv = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 210, 215, 225)), 2
    $g.DrawLine($pSilv, 125, 110, 150, 125)
    $g.DrawLine($pSilv, 195, 110, 170, 125)
    $g.DrawLine($pSilv, 108, 145, 125, 165)
    $g.DrawLine($pSilv, 212, 145, 195, 165)
    $g.DrawLine($pSilv, 150, 160, 160, 172)
    $g.DrawLine($pSilv, 170, 160, 160, 172)

    # Glowing silver-white eyes
    $bEye = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 235, 240, 255))
    $g.FillPolygon($bEye, @( (New-Object System.Drawing.Point 120, 135), (New-Object System.Drawing.Point 145, 130), (New-Object System.Drawing.Point 140, 142), (New-Object System.Drawing.Point 123, 142) ))
    $g.FillPolygon($bEye, @( (New-Object System.Drawing.Point 200, 135), (New-Object System.Drawing.Point 175, 130), (New-Object System.Drawing.Point 180, 142), (New-Object System.Drawing.Point 197, 142) ))

    $bSuit.Dispose(); $pPurl.Dispose(); $bSilv.Dispose(); $pSilv.Dispose(); $bEye.Dispose()
    Save-Avatar $c "static/avatars/avatar_33.png"
}

# -------------------------------------------------------------
# 34. Doctor Strange
# -------------------------------------------------------------
function Gen-34 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 145, 30, 25)) ([System.Drawing.Color]::FromArgb(255, 55, 15, 15))
    $g = $c.G

    # Cloak of Levitation High Collar
    $bCollar = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 195, 35, 30))
    $g.FillPolygon($bCollar, @(
        (New-Object System.Drawing.Point 80, 95),
        (New-Object System.Drawing.Point 60, 220),
        (New-Object System.Drawing.Point 260, 220),
        (New-Object System.Drawing.Point 240, 95),
        (New-Object System.Drawing.Point 205, 170),
        (New-Object System.Drawing.Point 115, 170)
    ))
    $bCollar.Dispose()

    # Blue Sorcerer Robe Body
    $bRobe = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 60, 130))
    $g.FillPolygon($bRobe, @( (New-Object System.Drawing.Point 50, 320), (New-Object System.Drawing.Point 75, 215), (New-Object System.Drawing.Point 245, 215), (New-Object System.Drawing.Point 270, 320) ))
    $bRobe.Dispose()

    # Eye of Agamotto Amulet (Gold with glowing green stone)
    $bGold = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 240, 190, 40))
    $g.FillEllipse($bGold, 142, 225, 36, 26)
    $bGreen = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 50, 225, 120))
    $g.FillEllipse($bGreen, 153, 233, 14, 10)
    $bGold.Dispose(); $bGreen.Dispose()

    # Neck
    $bSkin = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 205, 165))
    $g.FillRectangle($bSkin, 142, 175, 36, 40)

    # Head
    $g.FillEllipse($bSkin, 105, 75, 110, 125)

    # Dark Hair with Grey Temples
    $bHair = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 25, 25))
    $g.FillPie($bHair, 100, 55, 120, 95, 180, 180)
    $bGrey = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 200, 205, 215))
    $g.FillPie($bGrey, 98, 70, 25, 50, 90, 180)
    $g.FillPie($bGrey, 197, 70, 25, 50, 270, 180)
    $bHair.Dispose(); $bGrey.Dispose()

    # Goatee
    $bGoatee = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 35, 30, 30))
    $g.FillPolygon($bGoatee, @( (New-Object System.Drawing.Point 148, 165), (New-Object System.Drawing.Point 172, 165), (New-Object System.Drawing.Point 160, 188) ))
    $bGoatee.Dispose()

    # Eyes & Eyebrows
    $bEye = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 50, 50, 50))
    $g.FillEllipse($bEye, 128, 118, 10, 10)
    $g.FillEllipse($bEye, 182, 118, 10, 10)
    $pBrow = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 30, 25, 25)), 3
    $g.DrawLine($pBrow, 122, 108, 142, 112)
    $g.DrawLine($pBrow, 198, 108, 178, 112)

    $bSkin.Dispose(); $bEye.Dispose(); $pBrow.Dispose()
    Save-Avatar $c "static/avatars/avatar_34.png"
}

# -------------------------------------------------------------
# 35. Joker
# -------------------------------------------------------------
function Gen-35 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 75, 170, 45)) ([System.Drawing.Color]::FromArgb(255, 25, 80, 20))
    $g = $c.G

    # Purple Suit
    $bSuit = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 110, 35, 130))
    $g.FillPolygon($bSuit, @( (New-Object System.Drawing.Point 45, 320), (New-Object System.Drawing.Point 75, 220), (New-Object System.Drawing.Point 245, 220), (New-Object System.Drawing.Point 275, 320) ))

    # Orange Vest & Green Tie
    $bVest = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 240, 120, 20))
    $g.FillPolygon($bVest, @( (New-Object System.Drawing.Point 120, 320), (New-Object System.Drawing.Point 135, 235), (New-Object System.Drawing.Point 185, 235), (New-Object System.Drawing.Point 200, 320) ))
    $bTie = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 40, 180, 80))
    $g.FillPolygon($bTie, @( (New-Object System.Drawing.Point 155, 235), (New-Object System.Drawing.Point 165, 235), (New-Object System.Drawing.Point 160, 280) ))
    $bSuit.Dispose(); $bVest.Dispose(); $bTie.Dispose()

    # White Face & Neck
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 245, 250))
    $g.FillRectangle($bWhite, 140, 180, 40, 45)

    # Emerald Green Hair
    $bGreenHair = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 35, 185, 65))
    $g.FillEllipse($bGreenHair, 90, 45, 140, 110)
    # Hair tufts
    $g.FillPolygon($bGreenHair, @( (New-Object System.Drawing.Point 95, 75), (New-Object System.Drawing.Point 75, 40), (New-Object System.Drawing.Point 115, 60) ))
    $g.FillPolygon($bGreenHair, @( (New-Object System.Drawing.Point 225, 75), (New-Object System.Drawing.Point 245, 40), (New-Object System.Drawing.Point 205, 60) ))
    $g.FillPolygon($bGreenHair, @( (New-Object System.Drawing.Point 150, 50), (New-Object System.Drawing.Point 160, 20), (New-Object System.Drawing.Point 170, 50) ))

    # White Face
    $g.FillEllipse($bWhite, 105, 75, 110, 125)

    # Dark Eyes with arched purple brows
    $bEye = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillEllipse($bEye, 126, 115, 12, 12)
    $g.FillEllipse($bEye, 182, 115, 12, 12)
    $pBrow = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 80, 20, 100)), 3
    $g.DrawArc($pBrow, 120, 95, 25, 20, 190, 160)
    $g.DrawArc($pBrow, 175, 95, 25, 20, 190, 160)

    # Iconic Massive Red Grin with White Teeth
    $bRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 220, 20, 35))
    $g.FillPie($bRed, 115, 125, 90, 60, 0, 180)
    $bTeeth = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillPie($bTeeth, 122, 130, 76, 45, 0, 180)
    $pSmile = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 180, 10, 25)), 4
    $g.DrawArc($pSmile, 112, 120, 96, 68, 10, 160)
    # Tooth line
    $pTooth = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 200, 20, 30)), 1
    $g.DrawLine($pTooth, 135, 153, 185, 153)
    $g.DrawLine($pTooth, 150, 142, 150, 165)
    $g.DrawLine($pTooth, 160, 142, 160, 168)
    $g.DrawLine($pTooth, 170, 142, 170, 165)
    $pTooth.Dispose()

    $bWhite.Dispose(); $bGreenHair.Dispose(); $bEye.Dispose(); $pBrow.Dispose(); $bRed.Dispose(); $bTeeth.Dispose(); $pSmile.Dispose()
    Save-Avatar $c "static/avatars/avatar_35.png"
}

# -------------------------------------------------------------
# 36. Harley Quinn
# -------------------------------------------------------------
function Gen-36 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 240, 145, 185)) ([System.Drawing.Color]::FromArgb(255, 115, 205, 245))
    $g = $c.G

    # Body Jacket (Half Red / Half Black)
    $bRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 220, 30, 65))
    $bBlk = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillPolygon($bRed, @( (New-Object System.Drawing.Point 50, 320), (New-Object System.Drawing.Point 80, 220), (New-Object System.Drawing.Point 160, 220), (New-Object System.Drawing.Point 160, 320) ))
    $g.FillPolygon($bBlk, @( (New-Object System.Drawing.Point 160, 320), (New-Object System.Drawing.Point 160, 220), (New-Object System.Drawing.Point 240, 220), (New-Object System.Drawing.Point 270, 320) ))
    $bRed.Dispose(); $bBlk.Dispose()

    # Pigtails (Left Pink tip, Right Cyan tip)
    $bHair = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 240, 190))
    $g.FillEllipse($bHair, 80, 60, 160, 140)

    # Left Pigtail (Pink tip)
    $g.FillEllipse($bHair, 45, 60, 45, 80)
    $bPink = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 75, 145))
    $g.FillEllipse($bPink, 42, 105, 45, 55)
    $bPink.Dispose()

    # Right Pigtail (Cyan tip)
    $g.FillEllipse($bHair, 230, 60, 45, 80)
    $bCyan = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 45, 195, 245))
    $g.FillEllipse($bCyan, 233, 105, 45, 55)
    $bCyan.Dispose()

    # Face & Neck
    $bSkin = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 235, 220))
    $g.FillRectangle($bSkin, 140, 175, 40, 45)
    $g.FillEllipse($bSkin, 105, 75, 110, 120)

    # Blonde bangs
    $g.FillPie($bHair, 105, 65, 110, 60, 180, 180)
    $bHair.Dispose()

    # Sparkling Blue Eyes
    $bEye = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 40, 150, 230))
    $g.FillEllipse($bEye, 126, 118, 12, 14)
    $g.FillEllipse($bEye, 182, 118, 12, 14)
    $bEye.Dispose()

    # Small black heart on cheek
    $bHeart = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillEllipse($bHeart, 195, 142, 6, 6)
    $g.FillEllipse($bHeart, 200, 142, 6, 6)
    $g.FillPolygon($bHeart, @( (New-Object System.Drawing.Point 194, 145), (New-Object System.Drawing.Point 207, 145), (New-Object System.Drawing.Point 200, 153) ))
    $bHeart.Dispose()

    # Cute red lips
    $bLips = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 230, 30, 60))
    $g.FillEllipse($bLips, 145, 158, 30, 14)
    $bLips.Dispose(); $bSkin.Dispose()

    Save-Avatar $c "static/avatars/avatar_36.png"
}

# -------------------------------------------------------------
# 37. Darth Vader
# -------------------------------------------------------------
function Gen-37 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 180, 20, 20)) ([System.Drawing.Color]::FromArgb(255, 60, 5, 5))
    $g = $c.G

    # Shoulders / Cape
    $bArmor = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 25, 30))
    $g.FillPolygon($bArmor, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 75, 215), (New-Object System.Drawing.Point 245, 215), (New-Object System.Drawing.Point 280, 320) ))

    # Chest control box
    $bBox = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 45, 45, 50))
    $g.FillRectangle($bBox, 130, 250, 60, 45)
    $bGreen = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 50, 210, 80))
    $bRedBtn = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 230, 40, 40))
    $bSilv = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 200, 205, 215))
    $g.FillRectangle($bRedBtn, 138, 258, 12, 10)
    $g.FillRectangle($bGreen, 155, 258, 12, 10)
    $g.FillRectangle($bSilv, 172, 258, 12, 10)
    $bBox.Dispose(); $bGreen.Dispose(); $bRedBtn.Dispose(); $bSilv.Dispose()

    # Helmet Dome (flared outer rim)
    $g.FillPolygon($bArmor, @(
        (New-Object System.Drawing.Point 75, 170),
        (New-Object System.Drawing.Point 105, 65),
        (New-Object System.Drawing.Point 215, 65),
        (New-Object System.Drawing.Point 245, 170),
        (New-Object System.Drawing.Point 215, 185),
        (New-Object System.Drawing.Point 105, 185)
    ))
    $g.FillEllipse($bArmor, 100, 45, 120, 110)

    # Angular Mask Brow
    $bMask = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 35, 35, 40))
    $g.FillPolygon($bMask, @(
        (New-Object System.Drawing.Point 115, 105),
        (New-Object System.Drawing.Point 160, 118),
        (New-Object System.Drawing.Point 205, 105),
        (New-Object System.Drawing.Point 160, 130)
    ))

    # Dark Lenses
    $bLens = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 10, 10, 12))
    $g.FillEllipse($bLens, 120, 118, 26, 22)
    $g.FillEllipse($bLens, 174, 118, 26, 22)
    $bLens.Dispose()

    # Triangular Breathing Grill
    $g.FillPolygon($bMask, @(
        (New-Object System.Drawing.Point 160, 140),
        (New-Object System.Drawing.Point 135, 195),
        (New-Object System.Drawing.Point 185, 195)
    ))

    # Grill horizontal silver vents
    $pVent = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 160, 165, 175)), 2
    $g.DrawLine($pVent, 150, 160, 170, 160)
    $g.DrawLine($pVent, 144, 172, 176, 172)
    $g.DrawLine($pVent, 138, 184, 182, 184)
    $pVent.Dispose(); $bMask.Dispose(); $bArmor.Dispose()

    Save-Avatar $c "static/avatars/avatar_37.png"
}

# -------------------------------------------------------------
# 38. Homer Simpson
# -------------------------------------------------------------
function Gen-38 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 115, 185, 245)) ([System.Drawing.Color]::FromArgb(255, 65, 135, 215))
    $g = $c.G

    # White Polo Collar & Shirt
    $bShirt = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillPolygon($bShirt, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 85, 230), (New-Object System.Drawing.Point 235, 230), (New-Object System.Drawing.Point 280, 320) ))
    $pShirt = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 40)), 2
    $g.DrawLine($pShirt, 135, 230, 160, 265)
    $g.DrawLine($pShirt, 185, 230, 160, 265)
    $bShirt.Dispose(); $pShirt.Dispose()

    # Yellow Neck
    $bYel = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 215, 25))
    $g.FillRectangle($bYel, 135, 180, 50, 60)

    # Yellow Head (Dome)
    $g.FillEllipse($bYel, 110, 60, 100, 140)

    # 2 arched hair strands on top
    $pHair = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 40)), 3
    $g.DrawArc($pHair, 135, 40, 25, 30, 180, 180)
    $g.DrawArc($pHair, 155, 42, 25, 30, 180, 180)

    # Ear & 'M' side hair
    $g.FillEllipse($bYel, 95, 135, 20, 24)
    $pEar = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 40)), 2
    $g.DrawArc($pEar, 95, 135, 20, 24, 90, 180)
    $g.DrawLines($pHair, @( (New-Object System.Drawing.Point 105, 120), (New-Object System.Drawing.Point 112, 112), (New-Object System.Drawing.Point 118, 122), (New-Object System.Drawing.Point 125, 112), (New-Object System.Drawing.Point 130, 120) ))
    $pHair.Dispose(); $pEar.Dispose()

    # Brown Stubble / Muzzle
    $bMuzzle = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 210, 160, 95))
    $g.FillEllipse($bMuzzle, 115, 135, 90, 70)
    $bMuzzle.Dispose()

    # Big Round Cartoon Eyes
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 35, 35, 40)), 2
    $g.FillEllipse($bWhite, 120, 98, 42, 42)
    $g.DrawEllipse($pEye, 120, 98, 42, 42)
    $g.FillEllipse($bWhite, 155, 98, 42, 42)
    $g.DrawEllipse($pEye, 155, 98, 42, 42)

    # Pupils
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillEllipse($bPupil, 142, 115, 8, 8)
    $g.FillEllipse($bPupil, 172, 115, 8, 8)

    # Round Nose
    $g.FillEllipse($bYel, 142, 126, 24, 20)
    $g.DrawEllipse($pEye, 142, 126, 24, 20)

    # Smile line
    $pMouth = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 40)), 2
    $g.DrawArc($pMouth, 130, 155, 60, 30, 10, 150)

    $bYel.Dispose(); $bWhite.Dispose(); $pEye.Dispose(); $bPupil.Dispose(); $pMouth.Dispose()
    Save-Avatar $c "static/avatars/avatar_38.png"
}

# -------------------------------------------------------------
# 39. Rick Sanchez
# -------------------------------------------------------------
function Gen-39 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 50, 195, 135)) ([System.Drawing.Color]::FromArgb(255, 20, 95, 60))
    $g = $c.G

    # White Lab Coat & Teal Shirt
    $bCoat = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillPolygon($bCoat, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 75, 220), (New-Object System.Drawing.Point 245, 220), (New-Object System.Drawing.Point 280, 320) ))
    $bTeal = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 115, 200, 200))
    $g.FillPolygon($bTeal, @( (New-Object System.Drawing.Point 130, 320), (New-Object System.Drawing.Point 140, 230), (New-Object System.Drawing.Point 180, 230), (New-Object System.Drawing.Point 190, 320) ))
    $bCoat.Dispose(); $bTeal.Dispose()

    # Pale Skin Neck & Head
    $bSkin = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 238, 235, 225))
    $g.FillRectangle($bSkin, 145, 185, 30, 45)

    # Spiky Light-Blue Hair (Burst of spikes)
    $bHair = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 175, 215, 240))
    $pHair = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 140, 180, 210)), 2
    $spikes = @(
        (New-Object System.Drawing.Point 90, 160),
        (New-Object System.Drawing.Point 50, 135),
        (New-Object System.Drawing.Point 85, 115),
        (New-Object System.Drawing.Point 45, 80),
        (New-Object System.Drawing.Point 95, 75),
        (New-Object System.Drawing.Point 75, 35),
        (New-Object System.Drawing.Point 125, 45),
        (New-Object System.Drawing.Point 160, 15),
        (New-Object System.Drawing.Point 195, 45),
        (New-Object System.Drawing.Point 245, 35),
        (New-Object System.Drawing.Point 225, 75),
        (New-Object System.Drawing.Point 275, 80),
        (New-Object System.Drawing.Point 235, 115),
        (New-Object System.Drawing.Point 270, 135),
        (New-Object System.Drawing.Point 230, 160)
    )
    $g.FillPolygon($bHair, $spikes)
    $g.DrawPolygon($pHair, $spikes)

    # Head Oval
    $g.FillEllipse($bSkin, 115, 65, 90, 135)
    $pHead = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 160, 160, 160)), 2
    $g.DrawEllipse($pHead, 115, 65, 90, 135)

    # Cyan Unibrow
    $pBrow = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 145, 200, 230)), 4
    $g.DrawArc($pBrow, 130, 95, 60, 15, 190, 160)

    # Eyes (Heavy eyelids)
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 40)), 2
    $g.FillEllipse($bWhite, 126, 108, 30, 30); $g.DrawEllipse($pEye, 126, 108, 30, 30)
    $g.FillEllipse($bWhite, 164, 108, 30, 30); $g.DrawEllipse($pEye, 164, 108, 30, 30)
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillEllipse($bPupil, 139, 121, 5, 5)
    $g.FillEllipse($bPupil, 177, 121, 5, 5)

    # Nose & Mouth line
    $pLine = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 40)), 2
    $g.DrawLine($pLine, 158, 135, 162, 146)
    $g.DrawLine($pLine, 144, 165, 176, 165)

    # Green Drool
    $bDrool = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 120, 220, 50))
    $g.FillEllipse($bDrool, 168, 165, 7, 10)

    $bSkin.Dispose(); $bHair.Dispose(); $pHair.Dispose(); $pHead.Dispose(); $pBrow.Dispose(); $bWhite.Dispose(); $pEye.Dispose(); $bPupil.Dispose(); $pLine.Dispose(); $bDrool.Dispose()
    Save-Avatar $c "static/avatars/avatar_39.png"
}

# -------------------------------------------------------------
# 40. Morty Smith
# -------------------------------------------------------------
function Gen-40 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 245, 185, 40)) ([System.Drawing.Color]::FromArgb(255, 215, 130, 15))
    $g = $c.G

    # Yellow T-Shirt
    $bShirt = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 225, 40))
    $g.FillPolygon($bShirt, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 75, 220), (New-Object System.Drawing.Point 245, 220), (New-Object System.Drawing.Point 280, 320) ))
    $bShirt.Dispose()

    # Skin Neck
    $bSkin = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 250, 215, 180))
    $g.FillRectangle($bSkin, 145, 185, 30, 45)

    # Brown Round Hair
    $bHair = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 140, 95, 55))
    $g.FillEllipse($bHair, 100, 55, 120, 115)

    # Round Head
    $g.FillEllipse($bSkin, 105, 75, 110, 115)
    $pHead = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 180, 140, 110)), 2
    $g.DrawEllipse($pHead, 105, 75, 110, 115)

    # Brown Hair Fringe
    $g.FillPie($bHair, 102, 65, 116, 50, 180, 180)
    $bHair.Dispose()

    # Worried Wide Eyes
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 35, 35, 40)), 2
    $g.FillEllipse($bWhite, 124, 105, 32, 32); $g.DrawEllipse($pEye, 124, 105, 32, 32)
    $g.FillEllipse($bWhite, 164, 105, 32, 32); $g.DrawEllipse($pEye, 164, 105, 32, 32)

    # Tiny anxious pupils
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillEllipse($bPupil, 138, 119, 5, 5)
    $g.FillEllipse($bPupil, 178, 119, 5, 5)

    # Small curved nose & squiggly mouth
    $pLine = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 40)), 2
    $g.DrawArc($pLine, 154, 128, 12, 10, 200, 180)
    $g.DrawArc($pLine, 145, 152, 30, 12, 20, 140)

    $bSkin.Dispose(); $pHead.Dispose(); $bWhite.Dispose(); $pEye.Dispose(); $bPupil.Dispose(); $pLine.Dispose()
    Save-Avatar $c "static/avatars/avatar_40.png"
}

# -------------------------------------------------------------
# 41. Shrek
# -------------------------------------------------------------
function Gen-41 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 105, 135, 65)) ([System.Drawing.Color]::FromArgb(255, 50, 75, 30))
    $g = $c.G

    # Brown Burlap Vest & White Shirt
    $bShirt = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 235, 225, 205))
    $g.FillPolygon($bShirt, @( (New-Object System.Drawing.Point 35, 320), (New-Object System.Drawing.Point 70, 215), (New-Object System.Drawing.Point 250, 215), (New-Object System.Drawing.Point 285, 320) ))
    $bVest = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 120, 75, 40))
    $g.FillPolygon($bVest, @( (New-Object System.Drawing.Point 35, 320), (New-Object System.Drawing.Point 70, 215), (New-Object System.Drawing.Point 120, 215), (New-Object System.Drawing.Point 95, 320) ))
    $g.FillPolygon($bVest, @( (New-Object System.Drawing.Point 285, 320), (New-Object System.Drawing.Point 250, 215), (New-Object System.Drawing.Point 200, 215), (New-Object System.Drawing.Point 225, 320) ))
    $bShirt.Dispose(); $bVest.Dispose()

    # Ogre Green Skin
    $bGreen = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 150, 190, 70))
    $g.FillRectangle($bGreen, 130, 185, 60, 45) # wide neck

    # Funnel / Trumpet Ears
    $g.FillPolygon($bGreen, @( (New-Object System.Drawing.Point 95, 95), (New-Object System.Drawing.Point 45, 65), (New-Object System.Drawing.Point 50, 80), (New-Object System.Drawing.Point 95, 110) ))
    $g.FillPolygon($bGreen, @( (New-Object System.Drawing.Point 225, 95), (New-Object System.Drawing.Point 275, 65), (New-Object System.Drawing.Point 270, 80), (New-Object System.Drawing.Point 225, 110) ))
    $bDarkG = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 105, 145, 45))
    $g.FillEllipse($bDarkG, 42, 62, 14, 20)
    $g.FillEllipse($bDarkG, 264, 62, 14, 20)
    $bDarkG.Dispose()

    # Bulbous Head
    $g.FillEllipse($bGreen, 95, 65, 130, 135)

    # Cheerful Brow Ridge & Eyes
    $pBrow = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 115, 155, 50)), 4
    $g.DrawArc($pBrow, 118, 95, 32, 15, 180, 180)
    $g.DrawArc($pBrow, 170, 95, 32, 15, 180, 180)

    $bEye = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 75, 45, 20))
    $g.FillEllipse($bEye, 128, 110, 12, 12)
    $g.FillEllipse($bEye, 180, 110, 12, 12)

    # Wide Ogre Nose
    $g.FillEllipse($bGreen, 142, 122, 36, 26)
    $pLine = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 105, 145, 45)), 3
    $g.DrawArc($pLine, 142, 122, 36, 26, 10, 160)

    # Jolly Big Smile
    $pSmile = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 80, 115, 35)), 3
    $g.DrawArc($pSmile, 128, 145, 64, 30, 15, 150)

    $bGreen.Dispose(); $pBrow.Dispose(); $bEye.Dispose(); $pLine.Dispose(); $pSmile.Dispose()
    Save-Avatar $c "static/avatars/avatar_41.png"
}

# -------------------------------------------------------------
# 42. Bugs Bunny
# -------------------------------------------------------------
function Gen-42 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 250, 140, 40)) ([System.Drawing.Color]::FromArgb(255, 205, 85, 15))
    $g = $c.G

    # Grey Bunny Ears with Pink Inside
    $bGrey = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 165, 170, 180))
    $bPink = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 175, 195))
    $g.FillEllipse($bGrey, 110, 10, 36, 120)
    $g.FillEllipse($bPink, 116, 25, 24, 90)
    $g.FillEllipse($bGrey, 174, 10, 36, 120)
    $g.FillEllipse($bPink, 180, 25, 24, 90)
    $bPink.Dispose()

    # Shoulders
    $g.FillPolygon($bGrey, @( (New-Object System.Drawing.Point 60, 320), (New-Object System.Drawing.Point 100, 230), (New-Object System.Drawing.Point 220, 230), (New-Object System.Drawing.Point 260, 320) ))

    # Grey Head
    $g.FillEllipse($bGrey, 105, 90, 110, 115)

    # White Cheeks & Muzzle
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillEllipse($bWhite, 110, 135, 50, 45)
    $g.FillEllipse($bWhite, 160, 135, 50, 45)

    # Cartoon Eyes
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 45)), 2
    $g.FillEllipse($bWhite, 126, 105, 28, 40); $g.DrawEllipse($pEye, 126, 105, 28, 40)
    $g.FillEllipse($bWhite, 166, 105, 28, 40); $g.DrawEllipse($pEye, 166, 105, 28, 40)
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillEllipse($bPupil, 138, 122, 10, 16)
    $g.FillEllipse($bPupil, 172, 122, 10, 16)
    $bPupil.Dispose()

    # Cute Pink Nose
    $bNose = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 240, 115, 140))
    $g.FillEllipse($bNose, 150, 140, 20, 14)
    $bNose.Dispose()

    # Buck Teeth
    $g.FillRectangle($bWhite, 151, 174, 18, 16)
    $g.DrawRectangle($pEye, 151, 174, 18, 16)
    $g.DrawLine($pEye, 160, 174, 160, 190)

    # Smile
    $pSmile = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 45)), 2
    $g.DrawArc($pSmile, 132, 150, 56, 30, 15, 150)

    # Whiskers
    $g.DrawLine($pSmile, 115, 150, 85, 145)
    $g.DrawLine($pSmile, 115, 158, 85, 162)
    $g.DrawLine($pSmile, 205, 150, 235, 145)
    $g.DrawLine($pSmile, 205, 158, 235, 162)

    $bGrey.Dispose(); $bWhite.Dispose(); $pEye.Dispose(); $pSmile.Dispose()
    Save-Avatar $c "static/avatars/avatar_42.png"
}

# -------------------------------------------------------------
# 43. Mickey Mouse
# -------------------------------------------------------------
function Gen-43 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 235, 35, 45)) ([System.Drawing.Color]::FromArgb(255, 155, 15, 25))
    $g = $c.G

    # Red Pants Body
    $bRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 220, 25, 35))
    $g.FillPolygon($bRed, @( (New-Object System.Drawing.Point 45, 320), (New-Object System.Drawing.Point 85, 235), (New-Object System.Drawing.Point 235, 235), (New-Object System.Drawing.Point 275, 320) ))
    $bRed.Dispose()

    # White Oval Pants Buttons
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillEllipse($bWhite, 120, 260, 22, 34)
    $g.FillEllipse($bWhite, 178, 260, 22, 34)

    # Large Circular Black Ears
    $bBlack = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 25, 30))
    $g.FillEllipse($bBlack, 45, 25, 95, 95)
    $g.FillEllipse($bBlack, 180, 25, 95, 95)

    # Round Black Head
    $g.FillEllipse($bBlack, 95, 65, 130, 130)

    # Peach Face Mask
    $bPeach = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 220, 195))
    $g.FillEllipse($bPeach, 110, 95, 100, 95)
    $g.FillEllipse($bPeach, 115, 85, 45, 55)
    $g.FillEllipse($bPeach, 160, 85, 45, 55)

    # Tall Cartoon Eyes
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 25, 25, 30)), 2
    $g.FillEllipse($bWhite, 132, 95, 22, 36); $g.DrawEllipse($pEye, 132, 95, 22, 36)
    $g.FillEllipse($bWhite, 166, 95, 22, 36); $g.DrawEllipse($pEye, 166, 95, 22, 36)
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 25, 30))
    $g.FillEllipse($bPupil, 138, 112, 12, 18)
    $g.FillEllipse($bPupil, 170, 112, 12, 18)
    $bPupil.Dispose()

    # Oval Black Button Nose
    $g.FillEllipse($bBlack, 146, 132, 28, 18)

    # Happy Mouth with Red Tongue
    $bMouth = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 160, 20, 30))
    $g.FillPie($bMouth, 132, 145, 56, 40, 0, 180)
    $bTongue = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 100, 120))
    $g.FillPie($bTongue, 140, 162, 40, 22, 0, 180)
    $pSmile = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 25, 25, 30)), 3
    $g.DrawArc($pSmile, 128, 140, 64, 45, 20, 140)

    $bBlack.Dispose(); $bWhite.Dispose(); $bPeach.Dispose(); $pEye.Dispose(); $bMouth.Dispose(); $bTongue.Dispose(); $pSmile.Dispose()
    Save-Avatar $c "static/avatars/avatar_43.png"
}

# -------------------------------------------------------------
# 44. Donald Duck
# -------------------------------------------------------------
function Gen-44 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 25, 85, 175)) ([System.Drawing.Color]::FromArgb(255, 10, 45, 105))
    $g = $c.G

    # Blue Sailor Shirt & Red Bowtie
    $bShirt = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 95, 195))
    $g.FillPolygon($bShirt, @( (New-Object System.Drawing.Point 45, 320), (New-Object System.Drawing.Point 80, 220), (New-Object System.Drawing.Point 240, 220), (New-Object System.Drawing.Point 275, 320) ))
    $bShirt.Dispose()

    # Red Bowtie
    $bRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 225, 25, 35))
    $g.FillPolygon($bRed, @( (New-Object System.Drawing.Point 160, 240), (New-Object System.Drawing.Point 130, 220), (New-Object System.Drawing.Point 130, 260) ))
    $g.FillPolygon($bRed, @( (New-Object System.Drawing.Point 160, 240), (New-Object System.Drawing.Point 190, 220), (New-Object System.Drawing.Point 190, 260) ))
    $g.FillEllipse($bRed, 153, 233, 14, 14)
    $bRed.Dispose()

    # White Feathered Head & Neck
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillRectangle($bWhite, 140, 180, 40, 45)
    $g.FillEllipse($bWhite, 100, 75, 120, 120)

    # Blue Sailor Cap with Black Ribbon
    $bRibbon = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 25, 30))
    $g.FillPolygon($bRibbon, @( (New-Object System.Drawing.Point 195, 65), (New-Object System.Drawing.Point 255, 85), (New-Object System.Drawing.Point 245, 110), (New-Object System.Drawing.Point 190, 75) ))
    $bRibbon.Dispose()

    $bCap = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 20, 75, 175))
    $g.FillEllipse($bCap, 120, 45, 80, 36)
    $bGold = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 195, 30))
    $g.FillRectangle($bGold, 128, 68, 64, 8)
    $bCap.Dispose(); $bGold.Dispose()

    # Blue Eyes
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 30, 30, 35)), 2
    $g.FillEllipse($bWhite, 128, 90, 24, 38); $g.DrawEllipse($pEye, 128, 90, 24, 38)
    $g.FillEllipse($bWhite, 168, 90, 24, 38); $g.DrawEllipse($pEye, 168, 90, 24, 38)
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 105, 195))
    $g.FillEllipse($bPupil, 138, 104, 12, 18)
    $g.FillEllipse($bPupil, 170, 104, 12, 18)
    $bPupil.Dispose(); $pEye.Dispose()

    # Bright Yellow Duck Bill
    $bBill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 250, 170, 20))
    $g.FillEllipse($bBill, 105, 125, 110, 50)
    $pBill = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 210, 120, 10)), 3
    $g.DrawArc($pBill, 108, 138, 104, 32, 20, 140)

    $bWhite.Dispose(); $bBill.Dispose(); $pBill.Dispose()
    Save-Avatar $c "static/avatars/avatar_44.png"
}

# -------------------------------------------------------------
# 45. Patrick Star
# -------------------------------------------------------------
function Gen-45 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 30, 185, 205)) ([System.Drawing.Color]::FromArgb(255, 10, 115, 135))
    $g = $c.G

    # Green Hawaiian Shorts
    $bShorts = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 145, 220, 45))
    $g.FillPolygon($bShorts, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 65, 245), (New-Object System.Drawing.Point 255, 245), (New-Object System.Drawing.Point 280, 320) ))
    
    # Purple Floral Patterns on Shorts
    $bPurp = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 145, 55, 165))
    $g.FillEllipse($bPurp, 80, 265, 25, 25)
    $g.FillEllipse($bPurp, 150, 275, 28, 28)
    $g.FillEllipse($bPurp, 220, 260, 26, 26)
    $bShorts.Dispose(); $bPurp.Dispose()

    # Pointy Pink Starfish Head & Body
    $bPink = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 250, 155, 170))
    $g.FillPolygon($bPink, @(
        (New-Object System.Drawing.Point 160, 45),
        (New-Object System.Drawing.Point 195, 110),
        (New-Object System.Drawing.Point 235, 250),
        (New-Object System.Drawing.Point 85, 250),
        (New-Object System.Drawing.Point 125, 110)
    ))
    $g.FillEllipse($bPink, 142, 38, 36, 42) # rounded top point

    # Cheerful Dot Eyes with Arched Brows
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 30, 35))
    $g.FillEllipse($bPupil, 140, 115, 12, 16)
    $g.FillEllipse($bPupil, 168, 115, 12, 16)
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillEllipse($bWhite, 143, 118, 4, 5)
    $g.FillEllipse($bWhite, 171, 118, 4, 5)
    $bWhite.Dispose()

    # Cute little squiggly eyebrows
    $pBrow = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 45)), 2
    $g.DrawArc($pBrow, 136, 102, 18, 10, 180, 180)
    $g.DrawArc($pBrow, 166, 102, 18, 10, 180, 180)
    $pBrow.Dispose()

    # Big Joyful Open Mouth
    $bMouth = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 175, 25, 45))
    $g.FillPie($bMouth, 132, 145, 56, 50, 0, 180)
    $bTongue = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 120, 150))
    $g.FillPie($bTongue, 140, 168, 40, 26, 0, 180)
    $pSmile = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 140, 20, 35)), 2
    $g.DrawArc($pSmile, 130, 142, 60, 55, 15, 150)

    # Navel
    $pNavel = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 215, 115, 130)), 3
    $g.DrawArc($pNavel, 152, 222, 16, 10, 180, 180)

    $bPink.Dispose(); $bPupil.Dispose(); $bMouth.Dispose(); $bTongue.Dispose(); $pSmile.Dispose(); $pNavel.Dispose()
    Save-Avatar $c "static/avatars/avatar_45.png"
}

# -------------------------------------------------------------
# 46. Squidward Tentacles
# -------------------------------------------------------------
function Gen-46 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 20, 95, 125)) ([System.Drawing.Color]::FromArgb(255, 10, 50, 70))
    $g = $c.G

    # Brown Polo Shirt
    $bShirt = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 160, 105, 55))
    $g.FillPolygon($bShirt, @( (New-Object System.Drawing.Point 45, 320), (New-Object System.Drawing.Point 85, 225), (New-Object System.Drawing.Point 235, 225), (New-Object System.Drawing.Point 275, 320) ))
    $bShirt.Dispose()

    # Cyan / Teal Squid Skin
    $bTeal = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 140, 195, 180))
    $g.FillRectangle($bTeal, 144, 180, 32, 50) # skinny neck

    # Bulbous Bald Head
    $g.FillEllipse($bTeal, 95, 60, 130, 135)

    # Purple/Dark spots on forehead
    $bSpot = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 110, 165, 150))
    $g.FillEllipse($bSpot, 125, 75, 12, 10)
    $g.FillEllipse($bSpot, 145, 70, 14, 12)
    $g.FillEllipse($bSpot, 170, 78, 12, 10)
    $bSpot.Dispose()

    # Flat Oval Eyes with Yellow Tint & Rectangular Pupils
    $bYellow = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 235, 170))
    $pEye = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 35, 35, 40)), 2
    $g.FillEllipse($bYellow, 120, 100, 36, 42); $g.DrawEllipse($pEye, 120, 100, 36, 42)
    $g.FillEllipse($bYellow, 164, 100, 36, 42); $g.DrawEllipse($pEye, 164, 100, 36, 42)

    # Rectangular pupils
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 120, 40, 30))
    $g.FillRectangle($bPupil, 132, 116, 12, 10)
    $g.FillRectangle($bPupil, 176, 116, 12, 10)

    # Heavy drooping eyelids
    $g.FillPie($bTeal, 120, 96, 36, 30, 180, 180)
    $g.FillPie($bTeal, 164, 96, 36, 30, 180, 180)
    $g.DrawLine($pEye, 120, 111, 156, 111)
    $g.DrawLine($pEye, 164, 111, 200, 111)

    # Big Droopy Nose
    $g.FillEllipse($bTeal, 144, 120, 32, 55)
    $pLine = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 100, 160, 145)), 3
    $g.DrawArc($pLine, 144, 120, 32, 55, 10, 160)

    # Flat unamused mouth line
    $pMouth = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 40, 40, 45)), 3
    $g.DrawLine($pMouth, 135, 182, 185, 182)

    $bTeal.Dispose(); $bYellow.Dispose(); $pEye.Dispose(); $bPupil.Dispose(); $pLine.Dispose(); $pMouth.Dispose()
    Save-Avatar $c "static/avatars/avatar_46.png"
}

# -------------------------------------------------------------
# 47. Luigi
# -------------------------------------------------------------
function Gen-47 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 240, 165, 30)) ([System.Drawing.Color]::FromArgb(255, 195, 95, 10))
    $g = $c.G

    # Blue Dungarees & Green Shirt
    $bShirt = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 165, 60))
    $g.FillPolygon($bShirt, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 75, 220), (New-Object System.Drawing.Point 245, 220), (New-Object System.Drawing.Point 280, 320) ))
    
    # Overalls suspenders
    $bBlue = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 30, 80, 185))
    $g.FillRectangle($bBlue, 90, 240, 35, 80)
    $g.FillRectangle($bBlue, 195, 240, 35, 80)
    
    # Yellow Overall Buttons
    $bGold = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 250, 215, 30))
    $g.FillEllipse($bGold, 97, 260, 20, 20)
    $g.FillEllipse($bGold, 202, 260, 20, 20)
    $bShirt.Dispose(); $bBlue.Dispose(); $bGold.Dispose()

    # Skin Face & Neck
    $bSkin = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 215, 180))
    $g.FillRectangle($bSkin, 140, 180, 40, 45)
    $g.FillEllipse($bSkin, 105, 85, 110, 115)

    # Rosy Cheeks
    $bBlush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 185, 160))
    $g.FillEllipse($bBlush, 95, 130, 26, 26)
    $g.FillEllipse($bBlush, 199, 130, 26, 26)
    $bBlush.Dispose()

    # Blue Eyes
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillEllipse($bWhite, 126, 110, 22, 30)
    $g.FillEllipse($bWhite, 172, 110, 22, 30)
    $bEye = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 35, 125, 215))
    $g.FillEllipse($bEye, 134, 118, 12, 16)
    $g.FillEllipse($bEye, 174, 118, 12, 16)
    $bWhite.Dispose(); $bEye.Dispose()

    # Big Peach Nose
    $g.FillEllipse($bSkin, 140, 120, 40, 32)
    $pLine = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 225, 165, 130)), 2
    $g.DrawEllipse($pLine, 140, 120, 40, 32)
    $pLine.Dispose()

    # Brown Moustache
    $bStache = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 60, 40, 30))
    $g.FillEllipse($bStache, 120, 142, 45, 20)
    $g.FillEllipse($bStache, 155, 142, 45, 20)
    $bStache.Dispose()

    # Green Cap with White 'L' Emblem
    $bGreenCap = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 165, 60))
    $g.FillPie($bGreenCap, 85, 45, 150, 95, 180, 180) # dome
    $g.FillEllipse($bGreenCap, 75, 75, 170, 45) # brim

    # White Circle Emblem
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillEllipse($bWhite, 142, 52, 36, 36)

    # Green 'L' Logo
    $font = New-Object System.Drawing.Font "Arial", 20, ([System.Drawing.FontStyle]::Bold)
    $bL = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 20, 140, 50))
    $g.DrawString("L", $font, $bL, 149, 53)

    $bSkin.Dispose(); $bGreenCap.Dispose(); $bWhite.Dispose(); $font.Dispose(); $bL.Dispose()
    Save-Avatar $c "static/avatars/avatar_47.png"
}

# -------------------------------------------------------------
# 48. Leonardo (TMNT)
# -------------------------------------------------------------
function Gen-48 {
    $c = New-Canvas ([System.Drawing.Color]::FromArgb(255, 25, 75, 145)) ([System.Drawing.Color]::FromArgb(255, 10, 35, 75))
    $g = $c.G

    # Turtle Shell & Chest Shoulders
    $bTurtle = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 70, 145, 45))
    $g.FillPolygon($bTurtle, @( (New-Object System.Drawing.Point 40, 320), (New-Object System.Drawing.Point 75, 220), (New-Object System.Drawing.Point 245, 220), (New-Object System.Drawing.Point 280, 320) ))
    
    # Yellow Plastron Chest
    $bChest = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 225, 190, 75))
    $g.FillPolygon($bChest, @( (New-Object System.Drawing.Point 105, 320), (New-Object System.Drawing.Point 125, 235), (New-Object System.Drawing.Point 195, 235), (New-Object System.Drawing.Point 215, 320) ))
    
    # Brown Katana Strap across chest
    $bStrap = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 115, 65, 30))
    $g.FillPolygon($bStrap, @( (New-Object System.Drawing.Point 75, 225), (New-Object System.Drawing.Point 95, 225), (New-Object System.Drawing.Point 215, 320), (New-Object System.Drawing.Point 195, 320) ))
    $bChest.Dispose(); $bStrap.Dispose()

    # Green Head & Neck
    $g.FillRectangle($bTurtle, 138, 180, 44, 45)
    $g.FillEllipse($bTurtle, 95, 70, 130, 130)

    # Blue Mask Ribbons trailing to the side
    $bBlueMask = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 125, 245))
    $g.FillPolygon($bBlueMask, @( (New-Object System.Drawing.Point 220, 125), (New-Object System.Drawing.Point 275, 145), (New-Object System.Drawing.Point 255, 160), (New-Object System.Drawing.Point 215, 140) ))
    $g.FillPolygon($bBlueMask, @( (New-Object System.Drawing.Point 220, 130), (New-Object System.Drawing.Point 270, 175), (New-Object System.Drawing.Point 250, 185), (New-Object System.Drawing.Point 215, 145) ))

    # Blue Eye Mask
    $g.FillRectangle($bBlueMask, 93, 112, 134, 38)
    $g.FillEllipse($bBlueMask, 90, 112, 40, 38)
    $g.FillEllipse($bBlueMask, 190, 112, 40, 38)

    # Mask Eyes
    $bWhite = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.FillEllipse($bWhite, 118, 120, 24, 22)
    $g.FillEllipse($bWhite, 178, 120, 24, 22)
    $bPupil = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 25, 25, 30))
    $g.FillEllipse($bPupil, 126, 126, 10, 10)
    $g.FillEllipse($bPupil, 184, 126, 10, 10)
    $bWhite.Dispose(); $bPupil.Dispose()

    # Turtle Nostrils
    $bNose = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 50, 115, 30))
    $g.FillEllipse($bNose, 151, 158, 5, 5)
    $g.FillEllipse($bNose, 164, 158, 5, 5)
    $bNose.Dispose()

    # Confident Smirk
    $pSmile = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 45, 100, 25)), 3
    $g.DrawArc($pSmile, 132, 165, 56, 18, 15, 150)

    $bTurtle.Dispose(); $bBlueMask.Dispose(); $pSmile.Dispose()
    Save-Avatar $c "static/avatars/avatar_48.png"
}

# Run all 18 generators
Write-Output "Generating avatars 31 through 48..."
Gen-31
Gen-32
Gen-33
Gen-34
Gen-35
Gen-36
Gen-37
Gen-38
Gen-39
Gen-40
Gen-41
Gen-42
Gen-43
Gen-44
Gen-45
Gen-46
Gen-47
Gen-48
Write-Output "All 18 avatars generated successfully!"
