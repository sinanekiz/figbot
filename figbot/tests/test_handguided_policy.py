import unittest
import torch
from ai.training.train_handguided_policy import VisualJointPolicy,fit,metrics


class PolicyTests(unittest.TestCase):
    def test_shape_finite_fit_and_state_dict_round_trip(self):
        torch.set_num_threads(1)
        image=torch.zeros(4,3,96,128);history=torch.full((4,3,6),1000.)
        target=torch.full((4,3,6),1010.);current=history[:,-1]
        indices=torch.arange(4)
        model=fit(image,history,target-current[:,None,:],indices,2,42)
        other=VisualJointPolicy().eval();other.load_state_dict(model.state_dict())
        with torch.no_grad():
            out=model(image,history)
            self.assertEqual(tuple(out.shape),(4,3,6))
            self.assertTrue(torch.isfinite(out).all())
            torch.testing.assert_close(out,other(image,history))
        result,_=metrics(model,image,history,target,current,indices)
        self.assertEqual(len(result['per_joint_mae_counts']),6)


if __name__=='__main__':unittest.main()
