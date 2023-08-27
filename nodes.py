import torch

Y_FLIP = "y_axis (left to right)"
X_FLIP = "x_axis (top to bottom)"


class LatentMirror:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "samples": ("LATENT",),
                "symmetry_axis": ([Y_FLIP, X_FLIP],),
                "flip_side": (["first", "last"],),
                # TODO: Implement feathering to blend the seam line
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "symmetry"

    CATEGORY = "latent/transform"

    def symmetry(self, samples, symmetry_axis, flip_side):
        original_s = samples["samples"].shape

        cropped = self._crop_half(samples, symmetry_axis, flip_side)
        flipped = self._flip(cropped, symmetry_axis)

        x_pad = 0
        y_pad = 0

        cropped_s = cropped["samples"].shape

        if symmetry_axis.startswith("x"):
            x_pad = 0
            if flip_side == "first":
                y_pad = cropped["samples"].shape[2] * 8
            else:
                y_pad = 0
        if symmetry_axis.startswith("y"):
            if flip_side == "first":
                x_pad = cropped["samples"].shape[3] * 8
            else:
                x_pad = 0
            y_pad = 0

        composited = self._composite(samples, flipped, x_pad, y_pad)

        return (composited,)

    def _crop_half(self, samples, symmetry_axis, flip_side):
        samples_copy = samples.copy()
        samples_data = samples["samples"]

        width = samples_data.shape[3] * 8
        height = samples_data.shape[2] * 8

        x = 0
        y = 0

        if symmetry_axis.startswith("x"):
            if flip_side == "first":
                y = 0
            else:
                y = height // 2
            return self._crop(samples_copy, width, height // 2, x, y)
        elif symmetry_axis.startswith("y"):
            if flip_side == "first":
                x = 0
                print("we shoud lool here")
            else:
                x = width // 2
            return self._crop(samples_copy, width // 2, height, x, y)
        else:
            raise Exception("Invalid symmetry_axis")

    def _crop(self, samples, width, height, x, y):
        s = samples.copy()
        samples = samples["samples"]
        x = x // 8
        y = y // 8

        # enfonce minimum size of 64
        if x > (samples.shape[3] - 8):
            x = samples.shape[3] - 8
        if y > (samples.shape[2] - 8):
            y = samples.shape[2] - 8

        new_height = height // 8
        new_width = width // 8
        to_x = new_width + x
        to_y = new_height + y
        s["samples"] = samples[:, :, y:to_y, x:to_x]
        return s

    def _flip(self, samples, symmetry_axis):
        s = samples.copy()
        if symmetry_axis.startswith("x"):
            s["samples"] = torch.flip(samples["samples"], dims=[2])
        elif symmetry_axis.startswith("y"):
            s["samples"] = torch.flip(samples["samples"], dims=[3])
        return s

    def _composite(self, samples_to, samples_from, x, y, composite_method="normal"):
        x = x // 8
        y = y // 8

        samples_out = samples_to.copy()
        s = samples_to["samples"].clone()
        samples_to = samples_to["samples"]
        samples_from = samples_from["samples"]
        s[
            :, :, y : y + samples_from.shape[2], x : x + samples_from.shape[3]
        ] = samples_from[:, :, : samples_to.shape[2] - y, : samples_to.shape[3] - x]
        samples_out["samples"] = s
        return samples_out

