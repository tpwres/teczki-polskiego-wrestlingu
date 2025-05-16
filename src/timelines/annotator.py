from .stripe import Stripe

class Annotator:
    def annotate(self, axis, row, stripe, index):
        # TODO
        axis.annotate(
            self.format_annotation(stripe),
            xy=(stripe.start, row),
            gid=f"ann-{row}-{index}",
            annotation_clip=False
        )

    def format_annotation(self, stripe: Stripe) -> str:
        if stripe.end.year == 2099:
            return f"since {stripe.start:%Y-%m}"
        else:
            return f"from {stripe.start:%Y-%m} to {stripe.end:%Y-%m}"
