from .stripe import Stripe

class Annotator:
    def annotate(self, axis, stripe, top, identifier, include_org):
        # TODO
        axis.annotate(
            stripe.annotation or self.format_annotation(stripe, include_org),
            xy=(stripe.start, top),
            xytext=(-5, 1.5), textcoords='offset fontsize',
            gid=identifier,
            bbox=dict(boxstyle='square', facecolor='#ff00ff', edgecolor='none'),
            annotation_clip=False,
            color='#ff00ff'
        )

    def format_annotation(self, stripe: Stripe, include_org: bool) -> str:
        if include_org:
            orgs = self.format_orgs(stripe)
        else:
            orgs = ''
        if stripe.end.year == 2099:
            return f"{orgs} since {stripe.start:%Y-%m}"
        else:
            return f"{orgs} from {stripe.start:%Y-%m} to {stripe.end:%Y-%m}"

    def format_orgs(self, stripe: Stripe) -> str:
        return ','.join(o.upper() for o in stripe.all_orgs)
