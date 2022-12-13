from __future__ import annotations

from typing import List
from typing import Optional
from typing import Tuple

import cv2
import numpy as np


class CameraModel:
    def __init__(
        self,
        k: Optional[np.array] = None,
        d: Optional[np.array] = None,
        height: Optional[int] = None,
        width: Optional[int] = None,
    ):

        self.k = k
        self.d = d
        self.height = height
        self.width = width

    def __eq__(self, other: "CameraModel") -> bool:
        return (
            self.height == other.height
            and self.width == other.width
            and (self.k == other.k).all()
            and (self.d == other.d).all()
        )

    def calibrate(
        self,
        height: int,
        width: int,
        object_points_list: List[np.array],
        image_points_list: List[np.array],
    ):

        assert len(object_points_list) == len(image_points_list)
        self.height = height
        self.width = width

        object_points_list = [
            object_points.astype(np.float32).reshape(-1, 3) for object_points in object_points_list
        ]
        image_points_list = [
            image_points.astype(np.float32).reshape(-1, 1, 2) for image_points in image_points_list
        ]

        _, self.k, self.d, rvecs, tvecs = cv2.calibrateCamera(
            object_points_list,
            image_points_list,
            (self.width, self.height),
            cameraMatrix=None,
            distCoeffs=None,
        )

    def get_pose(
        self,
        board_detection: Optional["BoardDetection"] = None,  # noqa F821
        object_points: Optional[np.array] = None,
        image_points: Optional[np.array] = None,
    ) -> Tuple[np.array, np.array]:

        if board_detection is not None and object_points is None and image_points is None:
            object_points = board_detection.get_flattened_object_points()
            image_points = board_detection.get_flattened_image_points()

        d = np.zeros((5,)) if self.d is None else self.d
        k = self.k

        _, rvec, tvec = cv2.solvePnP(object_points, image_points, k, d)

        return rvec, tvec

    def get_reprojection_erros(
        self,
        board_detection: Optional["BoardDetection"] = None,  # noqa F821
        object_points: Optional[np.array] = None,
        image_points: Optional[np.array] = None,
        rvec: Optional[np.array] = None,
        tvec: Optional[np.array] = None,
    ) -> float:

        if board_detection is not None and object_points is None and image_points is None:
            object_points = board_detection.get_flattened_object_points()
            image_points = board_detection.get_flattened_image_points()

        if rvec is None or tvec is None:
            rvec, tvec = self.get_pose(object_points=object_points, image_points=image_points)

        num_points, dim = object_points.shape
        projected_points, _ = cv2.projectPoints(object_points, rvec, tvec, self.k, self.d)
        projected_points = projected_points.reshape((num_points, 2))
        return projected_points - image_points

    def rectify(self, img: np.array) -> np.array:
        raise NotImplementedError
