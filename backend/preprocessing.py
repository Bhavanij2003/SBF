def Four_Point_Transform(image, pts):
    # Obtain a consistent order of points and unpack them individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute width and height of the new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[0] - bl[0]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[0] - tl[0]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[1] - br[1]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[1] - bl[1]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Calculate transformation matrix and warp perspective
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped
