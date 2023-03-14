from numpy import array
plugins_tensor = array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype='float32')


from numpy import sum
plugins_sum = sum(a=plugins_tensor, axis=1)


from inex.helpers import evaluate
plugins_item = evaluate(w=plugins_tensor, i=2, j=1, expression='w[i, j]')


from inex.helpers import assign
plugins_colors = assign(value={'coral': '#FF7F50', 'lime': '#BFFF00', 'mabel': '#D9F7FF'})


from inex.helpers import posit_args
plugins_choice1 = posit_args(modname=plugins_colors, attname='__getitem__', arguments=['lime'])


from copy import copy
plugins_choice2 = copy(x=plugins_colors)['coral']


from numpy import array
plugins_array = array


from inex.helpers import show
show(
    shape=plugins_tensor.shape,
    dtype=plugins_tensor.dtype,
    result=plugins_sum,
    value=plugins_item,
    color1=plugins_choice1,
    color2=plugins_choice2,
    color3=plugins_colors['mabel'],
    array=plugins_array,
    list=[plugins_tensor.shape, plugins_tensor.dtype, plugins_sum],
    dict={'shape': plugins_tensor.shape, 'dtype': plugins_tensor.dtype, 'result': plugins_sum},
)
